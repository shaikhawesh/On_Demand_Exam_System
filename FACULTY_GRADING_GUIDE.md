# Faculty Grading System Guide

## Overview
Faculty members can now grade student exam submissions directly through the system. This guide explains how the grading system works and how to use it.

## How Faculty Grading Works

### 1. Faculty Login
- Faculty members login through the Faculty Login page
- Only approved faculty members can access grading features
- Faculty can have assigned subjects for which they can grade

### 2. Access Grading Interface
After logging in:
1. Click on **"Faculty Dashboard"** 
2. Locate the exam records or navigate to **"Faculty Results"** section
3. You'll see a table showing all student exam submissions

### 3. Grade Student Exams

The Faculty Results page displays:
- **Student Name**: Username of the student who submitted the exam
- **Subject**: The subject of the exam
- **Exam Date**: When the exam was submitted
- **Attempt ID**: Unique identifier for this exam attempt
- **Marks Fields**: Where you can input grades
- **Remarks**: Additional feedback for the student

#### Steps to Grade an Exam:
1. **Locate the student's exam** in the table
2. **Enter Marks**: Input the marks obtained by the student
3. **Enter Max Marks**: Input the maximum marks possible
4. **Add Remarks** (Optional): Enter feedback or comments about the exam
5. **Click "Save"**: Submit the grade

### 4. Subject Assignment
- Faculty can only grade exams for their **assigned subjects**
- If a subject is not assigned to you, it will not appear in your list
- Contact the administrator to assign subjects to your account

### 5. Grade History
- Once a grade is saved, the system shows:
  - When the grade was last updated
  - Who graded it (faculty member's name)
  - Timestamp of the grading

## Features

### Real-time Feedback
- Visual confirmation when grades are saved
- Success notifications appear at the bottom-right of the screen
- Loading indicators show the system is processing

### Grade Persistence
- Grades are saved to the database immediately
- You can edit grades anytime by updating the values and clicking Save
- Previous grade history is maintained

### Filtered Subject Display
- Only shows exams for subjects assigned to you
- Assigned subjects are displayed at the top of the page
- If no subjects are assigned, you'll see a notification

## Grade Information Tracked

For each exam grade, the system records:
- **Student Username**: Who the exam belongs to
- **Subject**: Which subject was tested
- **Attempt ID**: Unique identifier for tracking
- **Marks Obtained**: The grade you assigned
- **Max Marks**: Total possible marks
- **Remarks**: Your feedback/comments
- **Graded By**: Your username
- **Timestamp**: When the grade was recorded

## Technical Details

### Database Model
Grades are stored in the `ExamResult` model with the following fields:
- `user`: Foreign key to the Student
- `subject`: Subject name
- `attempt_id`: Unique exam attempt identifier
- `semester`: Academic semester
- `exam_date`: Date the exam was taken
- `marks_obtained`: Grade awarded
- `max_marks`: Total possible marks
- `remarks`: Feedback
- `graded_by`: Faculty member's username
- `graded_at`: Timestamp

### API Endpoints
- `POST /faculty/results/` - Submit grades (primary method)
- `POST /api/submit_grade/` - Alternative API endpoint (if needed)

## Troubleshooting

### Issue: Can't see any exams to grade
**Solution**: 
- Check if you've logged in correctly as faculty
- Ask administrator to assign subjects to your account
- Ensure students have submitted exams for grading

### Issue: Can't grade exams for a specific subject
**Solution**:
- The subject may not be assigned to you
- Contact your administrator to assign the subject
- Only assigned subjects appear in your grading interface

### Issue: Grade not saving
**Solution**:
- Ensure you have filled in at least the student marks
- Check your internet connection
- Refresh the page and try again
- Contact administrator if problem persists

## Assignment to Subjects

Administrators assign subjects to faculty members using the admin dashboard:
1. Navigate to Admin Dashboard
2. Manage Faculty Subject Assignments
3. Assign subjects to faculty members
4. Faculty will immediately see those exams available for grading

## Example Workflow

1. **Admin** assigns Subject "Mathematics" to Faculty "Dr. Smith"
2. **Student** submits an exam for Mathematics
3. **Dr. Smith** logs in and sees the exam in the Faculty Results page
4. **Dr. Smith** enters marks (e.g., 85/100) and remarks (e.g., "Good attempt")
5. **Dr. Smith** clicks Save
6. The system records the grade
7. **Student** can view the grade in their results page

## Notes

- Grades are permanent once saved (though they can be edited)
- Only faculty assigned to a subject can grade exams for that subject
- The system prevents unauthorized grade submission through validation checks
- All grade activities are logged with timestamps and faculty member names
