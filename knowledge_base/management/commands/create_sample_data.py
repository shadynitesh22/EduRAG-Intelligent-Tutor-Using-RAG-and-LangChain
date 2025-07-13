from django.core.management.base import BaseCommand
from knowledge_base.models import Subject, Grade, TextbookContent, ContentChunk
from django.contrib.auth.models import User
import uuid

class Command(BaseCommand):
    help = 'Create sample data for testing the RAG tutor system'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample data...')
        
        # Create sample subjects
        subjects = []
        subject_names = ['Mathematics', 'Science', 'History', 'English', 'Geography']
        for name in subject_names:
            subject, created = Subject.objects.get_or_create(name=name)
            subjects.append(subject)
            if created:
                self.stdout.write(f'Created subject: {name}')
        
        # Create sample grades
        grades = []
        grade_levels = ['K', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10']
        for level in grade_levels:
            grade, created = Grade.objects.get_or_create(level=level)
            grades.append(grade)
            if created:
                self.stdout.write(f'Created grade: {level}')
        
        # Create sample textbook content
        sample_content = {
            'Mathematics': {
                'title': 'Basic Mathematics for Grade 5',
                'content': """
                Chapter 1: Introduction to Fractions
                
                Fractions are a way to represent parts of a whole. A fraction consists of two numbers: the numerator (top number) and the denominator (bottom number).
                
                For example, in the fraction 3/4:
                - 3 is the numerator
                - 4 is the denominator
                - This means we have 3 parts out of 4 total parts
                
                Chapter 2: Adding Fractions
                
                To add fractions with the same denominator, simply add the numerators and keep the denominator the same.
                
                Example: 1/4 + 2/4 = 3/4
                
                To add fractions with different denominators, you need to find a common denominator first.
                
                Chapter 3: Multiplication
                
                Multiplication is repeated addition. When you multiply 3 × 4, you are adding 3 four times: 3 + 3 + 3 + 3 = 12.
                
                The multiplication table helps you quickly find the product of two numbers.
                """
            },
            'Science': {
                'title': 'Introduction to Biology',
                'content': """
                Chapter 1: What is Biology?
                
                Biology is the study of living things. All living organisms share certain characteristics:
                - They are made of cells
                - They can grow and develop
                - They can reproduce
                - They can respond to their environment
                - They can obtain and use energy
                
                Chapter 2: The Cell
                
                The cell is the basic unit of life. All living things are made of one or more cells.
                
                Plant cells have:
                - Cell wall
                - Chloroplasts
                - Large central vacuole
                
                Animal cells have:
                - Cell membrane
                - Nucleus
                - Mitochondria
                
                Chapter 3: Ecosystems
                
                An ecosystem is a community of living organisms and their environment. Ecosystems can be as small as a pond or as large as a forest.
                
                Key components of ecosystems:
                - Producers (plants)
                - Consumers (animals)
                - Decomposers (bacteria, fungi)
                """
            }
        }
        
        # Create or get a user for the content
        user, created = User.objects.get_or_create(
            username='sample_user',
            defaults={'email': 'sample@example.com'}
        )
        if created:
            user.set_password('password123')
            user.save()
            self.stdout.write('Created sample user: sample_user')
        
        # Create sample textbooks and chunks
        for subject_name, data in sample_content.items():
            subject = Subject.objects.get(name=subject_name)
            grade = Grade.objects.get(level='5')
            
            textbook, created = TextbookContent.objects.get_or_create(
                title=data['title'],
                defaults={
                    'subject': subject,
                    'grade': grade,
                    'content_text': data['content'],
                    'uploaded_by': user,
                    'is_processed': True
                }
            )
            
            if created:
                self.stdout.write(f'Created textbook: {data["title"]}')
                
                # Create content chunks
                content_parts = data['content'].split('\n\n')
                for i, part in enumerate(content_parts):
                    if part.strip():
                        chunk = ContentChunk.objects.create(
                            textbook=textbook,
                            chunk_text=part.strip(),
                            chunk_index=i
                        )
                        self.stdout.write(f'Created chunk {i} for {data["title"]}')
        
        self.stdout.write(
            self.style.SUCCESS('Successfully created sample data!')
        )
        self.stdout.write('You can now test the chat functionality with questions about mathematics and biology.') 
from knowledge_base.models import Subject, Grade, TextbookContent, ContentChunk
from django.contrib.auth.models import User
import uuid

class Command(BaseCommand):
    help = 'Create sample data for testing the RAG tutor system'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample data...')
        
        # Create sample subjects
        subjects = []
        subject_names = ['Mathematics', 'Science', 'History', 'English', 'Geography']
        for name in subject_names:
            subject, created = Subject.objects.get_or_create(name=name)
            subjects.append(subject)
            if created:
                self.stdout.write(f'Created subject: {name}')
        
        # Create sample grades
        grades = []
        grade_levels = ['K', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10']
        for level in grade_levels:
            grade, created = Grade.objects.get_or_create(level=level)
            grades.append(grade)
            if created:
                self.stdout.write(f'Created grade: {level}')
        
        # Create sample textbook content
        sample_content = {
            'Mathematics': {
                'title': 'Basic Mathematics for Grade 5',
                'content': """
                Chapter 1: Introduction to Fractions
                
                Fractions are a way to represent parts of a whole. A fraction consists of two numbers: the numerator (top number) and the denominator (bottom number).
                
                For example, in the fraction 3/4:
                - 3 is the numerator
                - 4 is the denominator
                - This means we have 3 parts out of 4 total parts
                
                Chapter 2: Adding Fractions
                
                To add fractions with the same denominator, simply add the numerators and keep the denominator the same.
                
                Example: 1/4 + 2/4 = 3/4
                
                To add fractions with different denominators, you need to find a common denominator first.
                
                Chapter 3: Multiplication
                
                Multiplication is repeated addition. When you multiply 3 × 4, you are adding 3 four times: 3 + 3 + 3 + 3 = 12.
                
                The multiplication table helps you quickly find the product of two numbers.
                """
            },
            'Science': {
                'title': 'Introduction to Biology',
                'content': """
                Chapter 1: What is Biology?
                
                Biology is the study of living things. All living organisms share certain characteristics:
                - They are made of cells
                - They can grow and develop
                - They can reproduce
                - They can respond to their environment
                - They can obtain and use energy
                
                Chapter 2: The Cell
                
                The cell is the basic unit of life. All living things are made of one or more cells.
                
                Plant cells have:
                - Cell wall
                - Chloroplasts
                - Large central vacuole
                
                Animal cells have:
                - Cell membrane
                - Nucleus
                - Mitochondria
                
                Chapter 3: Ecosystems
                
                An ecosystem is a community of living organisms and their environment. Ecosystems can be as small as a pond or as large as a forest.
                
                Key components of ecosystems:
                - Producers (plants)
                - Consumers (animals)
                - Decomposers (bacteria, fungi)
                """
            }
        }
        
        # Create or get a user for the content
        user, created = User.objects.get_or_create(
            username='sample_user',
            defaults={'email': 'sample@example.com'}
        )
        if created:
            user.set_password('password123')
            user.save()
            self.stdout.write('Created sample user: sample_user')
        
        # Create sample textbooks and chunks
        for subject_name, data in sample_content.items():
            subject = Subject.objects.get(name=subject_name)
            grade = Grade.objects.get(level='5')
            
            textbook, created = TextbookContent.objects.get_or_create(
                title=data['title'],
                defaults={
                    'subject': subject,
                    'grade': grade,
                    'content_text': data['content'],
                    'uploaded_by': user,
                    'is_processed': True
                }
            )
            
            if created:
                self.stdout.write(f'Created textbook: {data["title"]}')
                
                # Create content chunks
                content_parts = data['content'].split('\n\n')
                for i, part in enumerate(content_parts):
                    if part.strip():
                        chunk = ContentChunk.objects.create(
                            textbook=textbook,
                            chunk_text=part.strip(),
                            chunk_index=i
                        )
                        self.stdout.write(f'Created chunk {i} for {data["title"]}')
        
        self.stdout.write(
            self.style.SUCCESS('Successfully created sample data!')
        )
        self.stdout.write('You can now test the chat functionality with questions about mathematics and biology.') 
 