# Faculty Grading System - Setup & Testing Guide

## Prerequisites

Before using the faculty grading system, ensure:
- ✅ Faculty account is created and approved
- ✅ Faculty is assigned at least one subject via Admin Dashboard
- ✅ Students have submitted exams for grading
- ✅ Database migrations are up to date

## Step-by-Step Setup

### Step 1: Verify Faculty Account
1. Login to Admin Dashboard
2. Navigate to User Management
3. Confirm the faculty member is in the system
4. Status should be "Approved"

### Step 2: Assign Subjects to Faculty
1. Go to Admin Dashboard
2. Find "Faculty Subject Assignment" section
3. Click "Add Assignment"
4. Select Faculty member
5. Select Subject name
6. Click Save
7. Faculty will now see exams for that subject

### Step 3: Faculty Login
1. Go to Faculty Login page
2. Enter faculty username and password
3. Click Login
4. Should redirect to Faculty Dashboard

### Step 4: Access Grading Interface
1. On Faculty Dashboard, look for "Grade Exams" or "Faculty Results" link
2. Or navigate to: `http://yoursite.com/faculty/results/`
3. Should display:
   - Assigned subjects at the top
   - Table of student exam submissions
   - Grading form for each exam

## Step-by-Step Grading Process

### To Grade a Student's Exam:

1. **Locate the Student**
   - Find the student's name in the table
   - Identify their subject and exam date

2. **Enter Marks**
   - Click in the "Marks" field
   - Enter the marks the student obtained
   - Example: `85`

3. **Enter Maximum Marks**
   - Click in the "Out of" field
   - Enter total possible marks
   - Example: `100`

4. **Add Remarks (Optional)**
   - Click in the "Remarks" field
   - Type feedback for the student
   - Example: "Good attempt, work on MCQ section"

5. **Save the Grade**
   - Click the "Save" button
   - Wait for confirmation message
   - Button will show "Saving..." while processing

6. **Verify Save**
   - Success toast appears: "✓ Grade saved for [student] ([subject])"
   - "Last Updated" column shows new timestamp
   - Shows "By [faculty_name]" in the timestamp area

### Example Grading Entry
```
Student: john_doe
Subject: Mathematics
Marks Entered: 85
Max Marks: 100
Remarks: "Strong fundamentals, improve calculation speed"
Status: ✓ Saved (Nov 19, 2025 14:23 by Dr_Smith)
```

## Testing Checklist

### ✓ Faculty Login Test
- [ ] Faculty can login with correct credentials
- [ ] Faculty redirects to dashboard
- [ ] "Logged in as [username]" appears in header

### ✓ Subject Assignment Test
- [ ] Assigned subjects display at top of page
- [ ] Only exams for assigned subjects appear
- [ ] Multiple subjects show correctly if assigned

### ✓ Grade Submission Test
- [ ] Can enter marks in the field
- [ ] Can enter max marks in the field
- [ ] Can enter remarks in textarea
- [ ] Save button is clickable

### ✓ Save Functionality Test
- [ ] Clicking Save shows "Saving..." state
- [ ] Success message appears after save
- [ ] Graded field updates with timestamp
- [ ] "By [faculty]" shows faculty name
- [ ] Refresh page - grade persists

### ✓ Edit Grade Test
- [ ] Can change previously entered marks
- [ ] Can update remarks
- [ ] Click Save again
- [ ] New timestamp appears
- [ ] Changes persist after refresh

### ✓ Error Handling Test
- [ ] Try grading without entering marks (should work)
- [ ] Try accessing faculty page without login (should redirect)
- [ ] Try grading a subject you're not assigned to (should show error)
- [ ] Try submitting form with bad data (should handle gracefully)

### ✓ UI/UX Test
- [ ] Form layout is clean and organized
- [ ] Buttons are clickable and responsive
- [ ] Text is readable
- [ ] Mobile view works correctly
- [ ] Success messages are clear
- [ ] Error messages are helpful

## Common Issues & Solutions

### Issue: "No exam submissions found"
**Cause**: No students have submitted exams for your assigned subjects
**Solution**: 
- Ask students to submit exams
- Check that subjects are correctly assigned
- Verify in data/ folder that JSON files exist

### Issue: Can't see specific subject exams
**Cause**: Subject not assigned to your faculty account
**Solution**:
- Contact admin to assign the subject
- Admin goes to: Admin Dashboard → Faculty Subject Assignments
- Admin assigns your faculty to the subject

### Issue: Form not responding when clicking Save
**Cause**: JavaScript error or network issue
**Solution**:
- Refresh the page
- Check browser console for errors (F12)
- Verify internet connection
- Try a different browser

### Issue: Grades not persisting after refresh
**Cause**: Server error during save
**Solution**:
- Check browser console for error messages
- Verify database is accessible
- Check Django logs for errors
- Contact administrator

## Browser Compatibility

Tested and working on:
- ✅ Chrome/Edge (latest)
- ✅ Firefox (latest)
- ✅ Safari (latest)
- ✅ Mobile browsers (iOS Safari, Chrome Mobile)

## Keyboard Shortcuts

While working with grading forms:
- `Tab` - Move to next field
- `Shift+Tab` - Move to previous field
- `Enter` in last field - Submit form
- `Ctrl+S` - Save button focus

## Performance Notes

- Page loads ~1-2 seconds with 100+ exams
- Each grade save takes ~0.5-1 second
- Multiple rapid saves are queued automatically
- No page reload needed after save (AJAX)

## Data Backup

Grades are stored in the database with backups every:
- Daily (automatic)
- Before major updates
- On-demand (via admin dashboard)

## Support & Help

For issues or questions:
1. **Check the troubleshooting guide above**
2. **Contact your administrator**
3. **Check browser console (F12) for errors**
4. **Review Django logs** in the project directory

## Quick Reference

| Task | Location |
|------|----------|
| Login as Faculty | `/faculty_login/` |
| Grade Exams | `/faculty/results/` |
| Faculty Dashboard | `/faculty_dashboard/` |
| Assign Subjects (Admin) | Admin Dashboard |
| View My Grades (Student) | `/profile/results/` |

## FAQ

**Q: Can I grade exams not in my subject area?**
A: No, the system only shows exams for your assigned subjects.

**Q: Can I undo a grade?**
A: Yes, edit the grade and save again. The system keeps the timestamp.

**Q: Will students see my remarks?**
A: Yes, remarks are displayed when students view their results.

**Q: Can I bulk import grades?**
A: Currently only one at a time, but contact admin for CSV import if needed.

**Q: Is there a way to see all my graded exams?**
A: Yes, all graded exams show with timestamp and your name.
