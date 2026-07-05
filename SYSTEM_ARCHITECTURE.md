# Architecture Diagram - Unlock Dates Management System

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Admin Dashboard (Frontend)                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Calendar Widget - Select & Publish Dates                   │  │
│  │  (Existing functionality - unchanged)                       │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                            ↓                                        │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Existing Slots Table (ENHANCED - NEW COLUMNS)               │  │
│  │ ┌────┬────────┬──────┬──────────┬────────┬────────┬──────┐  │  │
│  │ │Date│Subject │ Time │Capacity  │ Booked │ Active │Action│  │  │
│  │ ├────┼────────┼──────┼──────────┼────────┼────────┼──────┤  │  │
│  │ │2024│Python  │09-11 │   50     │  12    │  ✓     │Edit  │  │  │
│  │ │12-1│Prog    │      │          │        │        │De-act│  │  │
│  │ │5   │        │      │          │        │        │Delete│  │  │
│  │ ├────┼────────┼──────┼──────────┼────────┼────────┼──────┤  │  │
│  │ │2024│Java    │  —   │   —      │  8     │  ✗     │Edit  │  │  │
│  │ │12-1│        │      │          │        │        │Act   │  │  │
│  │ │6   │        │      │          │        │        │Delete│  │  │
│  │ └────┴────────┴──────┴──────────┴────────┴────────┴──────┘  │  │
│  │                                                              │  │
│  │  Action Buttons (Per Row):                                 │  │
│  │  • [Edit] → Opens prompts for subject/time/capacity       │  │
│  │  • [Deactivate/Activate] → Toggle status (instant)        │  │
│  │  • [Delete] → Remove slot with confirmation              │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
            ↓                    ↓                    ↓
       [Edit Click]      [Toggle Click]        [Delete Click]
            ↓                    ↓                    ↓
    ┌──────────────┐   ┌──────────────┐    ┌──────────────┐
    │ Multi-Prompt │   │ Confirm Box  │    │ Confirm Box  │
    │ Dialog       │   │ (AJAX)       │    │ (AJAX)       │
    └──────────────┘   └──────────────┘    └──────────────┘
            ↓                    ↓                    ↓
    POST /api/update   POST /api/deact    POST /api/delete
    _unlock_slot       _unlock_slot       _unlock_slot
            ↓                    ↓                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    Django Backend (API Layer)                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌───────────────────┐  ┌───────────────────┐  ┌──────────────┐   │
│  │  api_update_      │  │  api_deactivate_  │  │ api_delete_  │   │
│  │  unlock_slot()    │  │  unlock_slot()    │  │ unlock_slot()│   │
│  │                   │  │                   │  │              │   │
│  │ • Validate auth   │  │ • Toggle status   │  │ • Confirm    │   │
│  │ • Parse JSON      │  │ • Update DB       │  │ • Delete row │   │
│  │ • Update fields   │  │ • Return new val  │  │ • Cascade    │   │
│  │ • Save to DB      │  │                   │  │ • Return ok  │   │
│  └───────────────────┘  └───────────────────┘  └──────────────┘   │
│                                                                     │
│                   ┌──────────────────────────┐                     │
│                   │api_bulk_delete_unlock    │                     │
│                   │_slots()                  │                     │
│                   │                          │                     │
│                   │• Accept array of IDs     │                     │
│                   │• Delete all in query     │                     │
│                   │• Return count            │                     │
│                   └──────────────────────────┘                     │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      Django ORM Layer                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  UnlockSlot.objects.get(id=...) → Fetch                           │
│                    ↓                                                │
│  Update fields: subject, start_time, end_time, capacity           │
│                    ↓                                                │
│  slot.save() → Write to database                                  │
│                    ↓                                                │
│  For delete: slot.delete() → Cascades to bookings                │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      SQLite Database                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Table: app_unlockslot                                            │
│  ┌────┬──────┬─────────┬───────────┬──────────┬──────────┬────┐   │
│  │id  │date  │subject  │start_time │end_time  │capacity  │is_ │   │
│  │    │      │         │           │          │          │act │   │
│  │    │      │         │           │          │          │ive │   │
│  ├────┼──────┼─────────┼───────────┼──────────┼──────────┼────┤   │
│  │1   │2024- │Python   │09:00      │11:00     │50        │1   │   │
│  │    │12-15 │Prog     │           │          │          │    │   │
│  ├────┼──────┼─────────┼───────────┼──────────┼──────────┼────┤   │
│  │2   │2024- │Java     │NULL       │NULL      │NULL      │0   │   │
│  │    │12-16 │         │           │          │          │    │   │
│  └────┴──────┴─────────┴───────────┴──────────┴──────────┴────┘   │
│                                                                     │
│  Table: app_unlockbooking (Cascaded on delete)                    │
│  Bookings are removed when UnlockSlot is deleted                 │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow - Edit Operation

```
User clicks [Edit] button on slot row
            ↓
JavaScript captures slot_id and current values from table
            ↓
Show prompts one at a time:
  1. Subject? → "Python Prog"
  2. Capacity? → "50"
  3. Start time? → "09:00"
  4. End time? → "11:00"
            ↓
Collect all values into object:
{
  subject: "Python Programming",
  start_time: "09:00",
  end_time: "11:00",
  capacity: 50
}
            ↓
POST /api/update_unlock_slot/5/
Headers: Content-Type: application/json
         X-CSRFToken: <token>
Body: {object above}
            ↓
Django receives request:
  ✓ Check CSRF token valid
  ✓ Check user.is_staff
  ✓ Parse JSON body
  ✓ Get UnlockSlot by ID
  ✓ Update each field (if provided)
  ✓ Save to database
            ↓
Return response:
{
  success: true,
  message: "Slot updated",
  slot: {
    id: 5,
    date: "2024-12-15",
    subject: "Python Programming",
    start_time: "09:00",
    end_time: "11:00",
    capacity: 50,
    is_active: true
  }
}
            ↓
JavaScript receives response:
  ✓ If success: show alert "Slot updated successfully"
  ✓ Reload page to refresh table with new data
```

---

## Data Flow - Toggle Activation

```
User clicks [Deactivate] button on active slot row
            ↓
JavaScript captures slot_id
            ↓
POST /api/deactivate_unlock_slot/5/
Headers: X-CSRFToken: <token>
            ↓
Django receives request:
  ✓ Check CSRF token
  ✓ Check user.is_staff
  ✓ Get UnlockSlot by ID
  ✓ Toggle is_active: (true → false)
  ✓ Save to database
            ↓
Return response:
{
  success: true,
  is_active: false,
  message: "Slot deactivated"
}
            ↓
JavaScript receives response (NO PAGE RELOAD):
  ✓ Update button text: "Deactivate" → "Activate"
  ✓ Update status badge: green → red, "Active" → "Inactive"
  ✓ Show alert: "Slot deactivated"
            ↓
User sees immediate visual feedback without page refresh
```

---

## Data Flow - Delete Operation

```
User clicks [Delete] button on slot row
            ↓
JavaScript shows confirmation dialog:
"Are you sure you want to delete this slot? 
 Associated bookings will be removed."
            ↓
User clicks OK (or Cancel)
            ↓
If Cancel: Abort operation
If OK: Continue
            ↓
POST /api/delete_unlock_slot/5/
Headers: X-CSRFToken: <token>
            ↓
Django receives request:
  ✓ Check CSRF token
  ✓ Check user.is_staff
  ✓ Get UnlockSlot by ID
  ✓ Cascade delete:
    - Delete UnlockSlot record
    - Delete all UnlockBooking records for this slot (CASCADE FK)
  ✓ Return success response
            ↓
Return response:
{
  success: true,
  message: "Deleted slot for 2024-12-15"
}
            ↓
JavaScript receives response:
  ✓ Show alert: "Slot deleted successfully"
  ✓ Reload page to refresh table
            ↓
Page refreshes:
  - Slot removed from table
  - Bookings removed from database
```

---

## Component Interaction Diagram

```
┌────────────────────────────────────────────────────────────┐
│         Admin Dashboard Template (HTML)                    │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Calendar Section                                     │  │
│  │ (Existing - creates slots via api_admin_create_slots)│  │
│  └──────────────────────────────────────────────────────┘  │
│                          ↓                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Existing Slots Table                                 │  │
│  │ (NEW - displays with all fields)                     │  │
│  │                                                      │  │
│  │ Columns:                                             │  │
│  │ - Date (from slot.date)                             │  │
│  │ - Subject (from slot.subject - NEW FIELD)           │  │
│  │ - Time (from slot.start_time - slot.end_time)       │  │
│  │ - Capacity (from slot.capacity - NEW FIELD)         │  │
│  │ - Booked (from slot.bookings.count())               │  │
│  │ - Active (from slot.is_active)                      │  │
│  │ - Actions (buttons for Edit/Toggle/Delete)          │  │
│  │                                                      │  │
│  │ Buttons per row:                                     │  │
│  │ [Edit] [Deactivate/Activate] [Delete]              │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ JavaScript Event Handlers                            │  │
│  │                                                      │  │
│  │ 1. slot-delete-btn click handler                    │  │
│  │    → Confirm → Call /api/delete_unlock_slot/        │  │
│  │                                                      │  │
│  │ 2. slot-toggle-btn click handler                    │  │
│  │    → Call /api/deactivate_unlock_slot/              │  │
│  │    → Update UI in-place (no reload)                 │  │
│  │                                                      │  │
│  │ 3. slot-edit-btn click handler                      │  │
│  │    → Show prompts for each editable field           │  │
│  │    → Call /api/update_unlock_slot/                  │  │
│  │    → Reload page on success                         │  │
│  │                                                      │  │
│  │ Helper functions:                                    │  │
│  │ - getCookie(name) - Extract CSRF token              │  │
│  │ - All handlers use Fetch API (modern async)         │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                            │
└────────────────────────────────────────────────────────────┘
                             ↓↓↓
┌────────────────────────────────────────────────────────────┐
│         Django Views (Backend API)                         │
│                                                            │
│  • api_delete_unlock_slot(request, slot_id)              │
│  • api_deactivate_unlock_slot(request, slot_id)          │
│  • api_update_unlock_slot(request, slot_id)              │
│  • api_bulk_delete_unlock_slots(request)                 │
│                                                            │
│  Common logic in all endpoints:                           │
│  1. Check CSRF token                                      │
│  2. Verify user.is_staff OR session['is_site_admin']     │
│  3. Try-catch for database operations                     │
│  4. Return JSON response                                  │
│                                                            │
└────────────────────────────────────────────────────────────┘
                             ↓↓↓
┌────────────────────────────────────────────────────────────┐
│         Django ORM                                         │
│                                                            │
│  UnlockSlot Model (Enhanced):                             │
│  - id, date, is_active (existing)                         │
│  - subject, start_time, end_time, capacity (NEW)          │
│  - get_available_capacity() method (NEW)                  │
│                                                            │
│  Related Models:                                           │
│  - User (FK)                                               │
│  - UnlockBooking (reverse FK, cascades on delete)          │
│                                                            │
└────────────────────────────────────────────────────────────┘
                             ↓↓↓
┌────────────────────────────────────────────────────────────┐
│         SQLite Database                                    │
│                                                            │
│  app_unlockslot table:                                    │
│  id | date | subject | start_time | end_time | capacity  │
│                      |is_active | user_id                 │
│                                                            │
│  app_unlockbooking table:                                 │
│  id | unlock_slot_id | user_id | created_at (CASCADE)    │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

## Security Architecture

```
Request from Frontend
        ↓
┌─────────────────────────────┐
│ CSRF Token Verification     │
│ X-CSRFToken header check    │
│ vs session cookie           │
└─────────────────────────────┘
        ↓ (Pass: Continue | Fail: 403 Forbidden)
┌─────────────────────────────┐
│ Authentication Check        │
│ user.is_staff OR            │
│ session['is_site_admin']    │
└─────────────────────────────┘
        ↓ (Pass: Continue | Fail: 403 Unauthorized)
┌─────────────────────────────┐
│ Input Validation            │
│ Type checking               │
│ String sanitization         │
│ Range/format validation     │
└─────────────────────────────┘
        ↓ (Pass: Continue | Fail: 400 Bad Request)
┌─────────────────────────────┐
│ Database Operation          │
│ Try-Catch error handling    │
│ ORM parameterized queries   │
│ (prevents SQL injection)    │
└─────────────────────────────┘
        ↓
┌─────────────────────────────┐
│ Success Response (200)      │
│ {"success": true, "data"..} │
│ OR Error Response           │
│ Status: 400, 403, 404, 500  │
│ {"success": false, "error"} │
└─────────────────────────────┘
        ↓
Response sent to Frontend
(Frontend handles success/error)
```

---

## File Structure Changes

```
project/
  ├── app/
  │   ├── models.py ⟵ MODIFIED (UnlockSlot enhanced)
  │   ├── views.py ⟵ MODIFIED (4 new API endpoints)
  │   ├── urls.py ⟵ MODIFIED (4 new routes)
  │   └── migrations/
  │       └── 0014_unlockslot_*.py ⟵ NEW (Migration applied)
  │
  ├── templates/
  │   └── Admin_dashboard.html ⟵ MODIFIED (table + handlers)
  │
  ├── UNLOCK_DATES_ENHANCEMENTS.md ⟵ NEW
  ├── IMPLEMENTATION_STATUS.md ⟵ NEW (overwritten)
  ├── QUICK_REFERENCE_UNLOCK_DATES.md ⟵ NEW
  └── COMPLETION_SUMMARY.md ⟵ NEW (overwritten)
```

---

## Integration Points

```
Unlock Dates Management System
            ↓
    ┌───────┴───────┐
    ↓               ↓
Calendar      Faculty Dashboard
Publishing    (Views available slots)
Slots
    ↓               ↓
    └───────┬───────┘
            ↓
    Attendance Sheet
    Download (checks
    capacity in future)
```
