from typing import Dict, Any, Optional
from django.db import connection
from django.conf import settings
from protocol.gemini_client import GeminiClient
from knowledge_base.models import TextbookContent, Subject, Grade, ContentChunk
import logging
import re

logger = logging.getLogger('rag_tutor')

class SQLAgent:
    def __init__(self):
        self.gemini_client = GeminiClient()
        self.schema_info = self._get_schema_info()
    
    def natural_language_to_sql(self, question: str) -> Dict[str, Any]:
        """Convert natural language question to SQL query"""
        
        try:
            # Check if we have any data in the database
            total_textbooks = TextbookContent.objects.count()
            if total_textbooks == 0:
                return {
                    'sql_query': None,
                    'results': [],
                    'answer': "I don't have any textbook content in the database yet. Please upload some content using the upload form above, and then I'll be able to answer questions about the data.",
                    'success': False,
                    'error': 'No data available'
                }
            
            # Generate SQL query
            sql_query = self._generate_sql_query(question)
            
            # Validate and execute query
            results = self._execute_query(sql_query)
            
            # Generate natural language response
            response = self._generate_response(question, sql_query, results)
            
            return {
                'sql_query': sql_query,
                'results': results,
                'answer': response,
                'success': True
            }
            
        except Exception as e:
            logger.error(f"SQL agent error: {str(e)}")
            return {
                'sql_query': None,
                'results': None,
                'response': f"I couldn't process that question: {str(e)}",
                'success': False,
                'error': str(e)
            }
    
    def _generate_sql_query(self, question: str) -> str:
        """Generate SQL query from natural language"""
        
        prompt = f"""
You are an expert SQL generator. Convert the natural language question to a SQL query based on the schema below.

Database Schema:
{self.schema_info}

Rules:
1. Only use SELECT statements
2. Use proper JOIN syntax when needed
3. Include appropriate WHERE clauses
4. Use LIMIT when appropriate
5. Return only the SQL query without explanation

Question: {question}

SQL Query:"""
        
        response = self.gemini_client.generate_chat_response(prompt, max_tokens=200)
        
        # Extract SQL query (remove markdown formatting if present)
        sql_query = re.sub(r'```sql\n?|```\n?', '', response.strip())
        
        return sql_query
    
    def _execute_query(self, sql_query: str) -> list:
        """Execute SQL query safely"""
        
        # Security check - only allow SELECT statements
        if not sql_query.strip().upper().startswith('SELECT'):
            raise ValueError("Only SELECT statements are allowed")
        
        # Additional security checks
        forbidden_keywords = ['DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER', 'CREATE', 'TRUNCATE']
        query_upper = sql_query.upper()
        
        for keyword in forbidden_keywords:
            if keyword in query_upper:
                raise ValueError(f"Forbidden keyword detected: {keyword}")
        
        with connection.cursor() as cursor:
            cursor.execute(sql_query)
            columns = [col[0] for col in cursor.description]
            results = cursor.fetchall()
            
            # Convert to list of dictionaries
            return [dict(zip(columns, row)) for row in results]
    
    def _generate_response(self, question: str, sql_query: str, results: list) -> str:
        """Generate natural language response from SQL results"""
        
        prompt = f"""
Convert the SQL query results into a natural language response.

Original Question: {question}
SQL Query: {sql_query}
Results: {results}

Provide a clear, concise answer based on the results. If no results were found, explain that appropriately.

Response:"""
        
        return self.gemini_client.generate_chat_response(prompt, max_tokens=300)
    
    def _get_schema_info(self) -> str:
        """Get database schema information"""
        
        return """
Tables:

1. knowledge_base_textbookcontent
   - id (UUID, Primary Key)
   - title (CharField)
   - subject_id (Foreign Key to knowledge_base_subject)
   - grade_id (Foreign Key to knowledge_base_grade)
   - uploaded_at (DateTimeField)
   - is_processed (BooleanField)

2. knowledge_base_subject
   - id (Integer, Primary Key)
   - name (CharField)
   - description (TextField)

3. knowledge_base_grade
   - id (Integer, Primary Key)
   - level (CharField - K, 1, 2, 3, etc.)
   - description (TextField)

4. knowledge_base_contentchunk
   - id (UUID, Primary Key)
   - textbook_id (Foreign Key to knowledge_base_textbookcontent)
   - chunk_text (TextField)
   - chunk_index (IntegerField)

5. knowledge_base_querylog
   - id (UUID, Primary Key)
   - query_text (TextField)
   - query_type (CharField)
   - created_at (DateTimeField)

Example queries:
- "How many textbooks are there?" -> SELECT COUNT(*) FROM knowledge_base_textbookcontent;
- "What subjects are available?" -> SELECT name FROM knowledge_base_subject;
- "How many textbooks per grade?" -> SELECT g.level, COUNT(*) FROM knowledge_base_textbookcontent t JOIN knowledge_base_grade g ON t.grade_id = g.id GROUP BY g.level;
"""