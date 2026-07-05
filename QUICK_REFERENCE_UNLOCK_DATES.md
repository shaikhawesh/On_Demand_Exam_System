# Quick Reference - Unlock Dates Management

## User Actions in Admin Dashboard

### 📋 View All Unlock Slots
**Location:** Admin Dashboard → Calendar/Unlock Dates section
**What you see:**
- Table with Date, Subject, Time, Capacity, Booked count, Active status
- Action buttons for each slot

### ✏️ Edit a Slot
1. Click **[Edit]** button on the slot row
2. Prompts appear one at a time:
   - Enter subject (or leave blank)
   - Enter capacity (or leave blank)
   - Enter start time (format: 09:00 or blank)
   - Enter end time (format: 17:00 or blank)
3. Confirm each prompt
4. Page refreshes to show updates

### 🟢 Deactivate a Slot
1. Click **[Deactivate]** button on active slot
2. Status updates instantly (no reload)
3. Button changes to **[Activate]**
4. Badge turns red and shows "Inactive"

### 🟡 Reactivate a Slot
1. Click **[Activate]** button on inactive slot
2. Status updates instantly
3. Button changes to **[Deactivate]**
4. Badge turns green and shows "Active"

### 🗑️ Delete a Slot
1. Click **[Delete]** button on the slot row
2. Confirmation dialog: "Are you sure you want to delete this slot? Associated bookings will be removed."
3. Click OK to confirm deletion
4. Slot is removed immediately, page refreshes

---

## API Endpoints Reference

### Delete a Slot
```bash
curl -X POST http://localhost:8000/api/delete_unlock_slot/5/ \
  -H "X-CSRFToken: YOUR_CSRF_TOKEN"
```

### Update a Slot
```bash
curl -X POST http://localhost:8000/api/update_unlock_slot/5/ \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: YOUR_CSRF_TOKEN" \
  -d '{
    "subject": "Python Programming",
    "start_time": "09:00",
    "end_time": "11:00",
    "capacity": 50
  }'
```

### Toggle Active Status
```bash
curl -X POST http://localhost:8000/api/deactivate_unlock_slot/5/ \
  -H "X-CSRFToken: YOUR_CSRF_TOKEN"
```

### Bulk Delete Slots
```bash
curl -X POST http://localhost:8000/api/bulk_delete_unlock_slots/ \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: YOUR_CSRF_TOKEN" \
  -d '{
    "slot_ids": [1, 2, 3, 4, 5]
  }'
```

---

## Table Column Descriptions

| Column | Description |
|--------|-------------|
| **Date** | The date when this unlock slot is available |
| **Subject** | Subject assigned to this slot (if any) |
| **Time** | Start time - End time for the slot (if configured) |
| **Capacity** | Maximum number of bookings allowed (blank = unlimited) |
| **Booked** | Current number of active bookings |
| **Active** | Status badge - Green = Active, Red = Inactive |
| **Actions** | Edit, Activate/Deactivate, Delete buttons |

---

## Keyboard Shortcuts & Tips

### Editing Multiple Fields
```
When editing a slot:
- Leave field blank to keep current value or remove it
- Press Escape to cancel any prompt
- Each field is optional - only fill what you want to change
```

### Quick Deactivate/Reactivate
```
Use Activate/Deactivate buttons for:
- Temporarily blocking a slot without deleting
- Preventing new bookings without losing historical data
- Administrative hold on a date
```

### Bulk Operations
```
To delete multiple slots efficiently:
1. Note the slot IDs
2. Use the API endpoint: /api/bulk_delete_unlock_slots/
3. Or implement checkbox UI in future update
```

---

## Common Scenarios

### Scenario 1: Block a Date Temporarily
**Action:** Click [Deactivate]
**Result:** Faculty cannot book, but slot data remains
**Reverse:** Click [Activate] to enable again

### Scenario 2: Add Subject to Existing Slot
**Action:** Click [Edit] → Enter subject name → Confirm
**Result:** Subject appears in table, helps categorize slots

### Scenario 3: Set Time Window for Slot
**Action:** Click [Edit] → Enter times → Confirm
**Result:** Faculty sees available time window (e.g., "09:00 - 11:00")

### Scenario 4: Limit Bookings per Slot
**Action:** Click [Edit] → Enter capacity → Confirm
**Result:** Maximum capacity enforced (feature ready for booking system)

### Scenario 5: Remove Outdated Slots
**Action:** Click [Delete] → Confirm → Slot removed
**Result:** All associated bookings also deleted

---

## Troubleshooting

### Button Not Responding
- **Check:** Is the page fully loaded?
- **Try:** Refresh the page
- **Check:** Are you logged in as admin/staff?

### Slot Didn't Update
- **Check:** Did the page reload after action?
- **Check:** Check browser console (F12 → Console tab)
- **Try:** Refresh page to see latest data

### Time Format Error
- **Format:** Use HH:mm (24-hour format)
- **Examples:** ✓ 09:00, ✓ 14:30, ✗ 9:0, ✗ 2:30 PM

### Deactivate Not Working
- **Check:** Are you clicking the orange button?
- **Try:** Refresh page if status seems stuck
- **Note:** Status updates without reload - wait a moment

---

## Database Info for Developers

### UnlockSlot Table Fields
```sql
id (PK)
date (DATE)
is_active (BOOLEAN) - Toggle status
subject (VARCHAR) - Nullable
start_time (TIME) - Nullable
end_time (TIME) - Nullable
capacity (INT) - Default: 0 (unlimited)
user_id (FK)
created_at (auto_now_add)
updated_at (auto_now)
```

### Model Method
```python
slot.get_available_capacity()
Returns: capacity - count(bookings)
```

---

## Migration History

**Migration 0014:** Added subject, start_time, end_time, capacity fields
- Status: Applied ✅
- Reversible: Yes
- Data loss: No (all fields nullable/have defaults)

---

## Feature Status

| Feature | Status | Notes |
|---------|--------|-------|
| Delete slot | ✅ Complete | Cascades bookings |
| Edit slot | ✅ Complete | All fields optional |
| Toggle active | ✅ Complete | No page reload |
| Capacity tracking | ✅ Complete | Ready for booking validation |
| Subject assignment | ✅ Complete | Helps categorize slots |
| Time slots | ✅ Complete | Shows availability window |
| Bulk delete API | ✅ Complete | Ready for batch operations |
| UI for bulk operations | 🔄 Planned | Add checkboxes to table |

---

## Support

For issues or questions:
1. Check UNLOCK_DATES_ENHANCEMENTS.md for detailed documentation
2. Review IMPLEMENTATION_STATUS.md for technical details
3. Check Django debug output (manage.py runserver output)
