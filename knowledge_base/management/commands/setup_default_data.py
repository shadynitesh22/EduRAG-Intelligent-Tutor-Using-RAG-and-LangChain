from django.core.management.base import BaseCommand
from knowledge_base.models import Subject, Grade
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Setup default subjects and grades for the RAG tutor system'

    def handle(self, *args, **options):
        self.stdout.write('Setting up default data...')
        
        # Create default subjects
        subjects_data = [
            {'name': 'Mathematics', 'description': 'Algebra, Geometry, Calculus, Statistics'},
            {'name': 'Science', 'description': 'Physics, Chemistry, Biology, Earth Science'},
            {'name': 'English', 'description': 'Literature, Grammar, Writing, Reading'},
            {'name': 'History', 'description': 'World History, US History, Ancient Civilizations'},
            {'name': 'Geography', 'description': 'Physical Geography, Human Geography, Maps'},
            {'name': 'Computer Science', 'description': 'Programming, Algorithms, Data Structures'},
            {'name': 'Art', 'description': 'Drawing, Painting, Digital Art, Art History'},
            {'name': 'Music', 'description': 'Music Theory, Instrumental, Vocal, Music History'},
            {'name': 'Physical Education', 'description': 'Sports, Fitness, Health Education'},
            {'name': 'Social Studies', 'description': 'Civics, Economics, Sociology, Psychology'},
        ]
        
        for subject_data in subjects_data:
            subject, created = Subject.objects.get_or_create(
                name=subject_data['name'],
                defaults={'description': subject_data['description']}
            )
            if created:
                self.stdout.write(f'✓ Created subject: {subject.name}')
            else:
                self.stdout.write(f'• Subject already exists: {subject.name}')
        
        # Create default grades
        grades_data = [
            {'level': 'K', 'description': 'Early childhood education'},
            {'level': '1', 'description': 'First grade elementary'},
            {'level': '2', 'description': 'Second grade elementary'},
            {'level': '3', 'description': 'Third grade elementary'},
            {'level': '4', 'description': 'Fourth grade elementary'},
            {'level': '5', 'description': 'Fifth grade elementary'},
            {'level': '6', 'description': 'Sixth grade middle school'},
            {'level': '7', 'description': 'Seventh grade middle school'},
            {'level': '8', 'description': 'Eighth grade middle school'},
            {'level': '9', 'description': 'Ninth grade high school'},
            {'level': '10', 'description': 'Tenth grade high school'},
            {'level': '11', 'description': 'Eleventh grade high school'},
            {'level': '12', 'description': 'Twelfth grade high school'},
        ]
        
        for grade_data in grades_data:
            grade, created = Grade.objects.get_or_create(
                level=grade_data['level'],
                defaults={'description': grade_data['description']}
            )
            if created:
                self.stdout.write(f'✓ Created grade: Grade {grade.level}')
            else:
                self.stdout.write(f'• Grade already exists: Grade {grade.level}')
        
        # Create default admin user if it doesn't exist
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
            self.stdout.write('✓ Created default admin user: admin/admin123')
        else:
            self.stdout.write('• Admin user already exists')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Setup complete! Created {Subject.objects.count()} subjects and {Grade.objects.count()} grades.'
            )
        ) 