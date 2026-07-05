# Faculty Grading System - Quick Start

## What's New?

Faculty members can now **grade student exams directly in the system**! 

## 5-Minute Quick Start

### For Faculty:

1. **Login** - Go to Faculty Login and enter credentials
2. **Navigate** - Click "Grade Exams" or go to Faculty Results
3. **View** - See all student exams for your assigned subjects
4. **Grade** - Enter marks, max marks, and remarks
5. **Save** - Click Save button
6. **Done** - See success confirmation!

### For Admins:

1. **Assign** - Go to Admin Dashboard
2. **Find** - "Faculty Subject Assignment" section
3. **Select** - Choose faculty and subject
4. **Save** - Click to assign
5. **Done** - Faculty can now grade those exams!

## Screenshot Flow

```
Faculty Dashboard
    ↓
Click "Grade Exams"
    ↓
See Student Exam List
    ↓
Enter: Marks | Max Marks | Remarks
    ↓
Click "Save"
    ↓
✓ Grade saved! (Success message)
    ↓
Timestamp appears showing when saved
```

## Key Features

- ✅ **Real-time Grading** - Save immediately, no page reload needed
- ✅ **Subject-Based Filtering** - Only see exams for your subjects
- ✅ **Edit Anytime** - Update grades if needed
- ✅ **Feedback** - Add remarks for students
- ✅ **Tracking** - See when each grade was saved and by whom
- ✅ **Mobile Friendly** - Works on phones and tablets

## Example Workflow

**Admin assigns "Math" to Dr. Smith**
↓
**Student submits Math exam**
↓
**Dr. Smith logs in → Sees exam**
↓
**Dr. Smith enters: 85/100 marks + remarks**
↓
**Dr. Smith clicks Save**
↓
**✓ Success! Grade is saved**
↓
**Student can see the grade in Results**

## Common Tasks

### Grade an Exam
1. Login as Faculty
2. Go to Faculty Results
3. Find the student in the table
4. Fill in Marks, Max Marks, and Remarks
5. Click Save

### Update an Existing Grade
1. Go to Faculty Results
2. Find the graded exam
3. Change the Marks/Remarks
4. Click Save again

### Check Your Assigned Subjects
1. Go to Faculty Results
2. Look at the top - Shows all your subjects
3. Only exams for these subjects appear

## If Something Goes Wrong

| Problem | Fix |
|---------|-----|
| Can't see any exams | Admin needs to assign you a subject |
| Save button not working | Refresh page and try again |
| Error message appears | Check that marks field is filled |
| Grade disappeared | Refresh page - it's still there |

## Files Changed

These files were updated to add grading:
- `app/views.py` - Added grade submission logic
- `app/urls.py` - Added `/api/submit_grade/` route
- `templates/Faculty_results.html` - Improved grading UI

## Need Help?

1. **Check**: Did you login as faculty?
2. **Check**: Does admin have your subject assigned?
3. **Check**: Are there student exams to grade?
4. **Ask**: Administrator for subject assignment
5. **Refresh**: The browser page and try again

## That's It!

You're all set to grade student exams. Start by logging in and visiting the Faculty Results page.

Questions? Check `FACULTY_GRADING_GUIDE.md` for detailed documentation.
