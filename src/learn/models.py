"""Learning module system for LFCS Practice Tool"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum

class ExerciseType(Enum):
    """Types of exercises"""
    COMMAND = "command"
    QUESTION = "question"
    TASK = "task"

class DifficultyLevel(Enum):
    """Learning difficulty levels"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"
    LFCS_PREP = "lfcs_prep"

@dataclass
class Exercise:
    """Interactive exercise within a lesson"""
    id: str
    description: str
    exercise_type: ExerciseType
    
    # For command exercises
    command: Optional[str] = None
    expected_output: Optional[str] = None
    expected_pattern: Optional[str] = None
    
    # For question exercises
    question: Optional[str] = None
    options: List[str] = field(default_factory=list)
    correct_answer: Optional[str] = None
    
    # Hints and validation
    hints: List[str] = field(default_factory=list)
    validation: Optional[Dict[str, Any]] = None
    points: int = 10
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Exercise':
        """Create Exercise from dictionary"""
        exercise_type = ExerciseType(data.get('type', 'command'))
        
        # Description is optional for questions (use question text)
        description = data.get('description')
        if not description and exercise_type == ExerciseType.QUESTION:
            description = data.get('question', 'Question')
            
        return cls(
            id=data['id'],
            description=description or "No description",
            exercise_type=exercise_type,
            command=data.get('command'),
            expected_output=data.get('expected_output'),
            expected_pattern=data.get('expected_pattern'),
            question=data.get('question'),
            options=data.get('options', []),
            correct_answer=data.get('correct_answer'),
            hints=data.get('hints', []),
            validation=data.get('validation'),
            points=data.get('points', 10)
        )

@dataclass
class Lesson:
    """A lesson within a learning module"""
    id: str
    title: str
    notes: str
    exercises: List[Exercise] = field(default_factory=list)
    estimated_time: int = 10  # minutes
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Lesson':
        """Create Lesson from dictionary"""
        exercises = [Exercise.from_dict(ex) for ex in data.get('exercises', [])]
        return cls(
            id=data['id'],
            title=data['title'],
            notes=data['notes'],
            exercises=exercises,
            estimated_time=data.get('estimated_time', 10)
        )

@dataclass
class LearningModule:
    """A complete learning module with multiple lessons"""
    id: str
    level: DifficultyLevel
    title: str
    description: str
    lessons: List[Lesson] = field(default_factory=list)
    estimated_time: int = 30  # minutes
    prerequisites: List[str] = field(default_factory=list)
    completion_criteria: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LearningModule':
        """Create LearningModule from dictionary"""
        level = DifficultyLevel(data.get('level', 'beginner'))
        lessons = [Lesson.from_dict(lesson) for lesson in data.get('lessons', [])]
        
        return cls(
            id=data['id'],
            level=level,
            title=data['title'],
            description=data['description'],
            lessons=lessons,
            estimated_time=data.get('estimated_time', 30),
            prerequisites=data.get('prerequisites', []),
            completion_criteria=data.get('completion_criteria', {})
        )
    
    def get_total_exercises(self) -> int:
        """Get total number of exercises in module"""
        return sum(len(lesson.exercises) for lesson in self.lessons)
    
    def get_total_points(self) -> int:
        """Get total points available in module"""
        total = 0
        for lesson in self.lessons:
            for exercise in lesson.exercises:
                total += exercise.points
        return total
