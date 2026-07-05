# Unlock Dates Management Enhancements

## Overview
Comprehensive improvements to the Unlock Dates functionality providing full CRUD operations and enhanced management capabilities.

## Changes Implemented

### 1. Database Model Enhancements
**File:** `app/models.py`
- Added 4 new fields to `UnlockSlot` model:
  - `subject` (CharField, optional) - Assign specific subject to each unlock slot
  - `start_time` (TimeField, optional) - Start time for the unlock window
  - `end_time` (TimeField, optional) - End time for the unlock window  
  - `capacity` (IntegerField, default=0) - Maximum booking capacity per slot
- Added `get_available_capacity()` method to calculate remaining available slots

### 2. API Endpoints
**File:** `app/views.py`
- **`api_delete_unlock_slot(request, slot_id)`** - DELETE single unlock slot
  - Requires admin/staff authentication
  - Cascades to remove associated bookings
  - Returns success/error message with deleted date

- **`api_deactivate_unlock_slot(request, slot_id)`** - TOGGLE active/inactive status
  - Toggle slot between active and inactive states
  - Doesn't delete, just deactivates for administrative control
  - Returns updated status

- **`api_update_unlock_slot(request, slot_id)`** - PATCH/UPDATE slot properties
  - Update: subject, start_time, end_time, capacity
  - All fields optional - only provided fields are updated
  - Validates and sanitizes input data
  - Returns updated slot details

- **`api_bulk_delete_unlock_slots(request)`** - DELETE multiple slots at once
  - Accepts array of slot IDs: `{ "slot_ids": [1,2,3] }`
  - Returns count of deleted slots
  - Enables efficient bulk cleanup operations

### 3. URL Routes
**File:** `app/urls.py`
Added routes for all new API endpoints:
```
/api/delete_unlock_slot/<int:slot_id>/
/api/deactivate_unlock_slot/<int:slot_id>/
/api/update_unlock_slot/<int:slot_id>/
/api/bulk_delete_unlock_slots/
```

### 4. Enhanced UI/Table
**File:** `templates/Admin_dashboard.html`

#### Updated Existing Slots Table
Displays comprehensive slot information with action buttons:
- **Columns:**
  - Date (when the slot is available)
  - Subject (assigned subject, if any)
  - Time (start_time - end_time, if configured)
  - Capacity (maximum bookings allowed)
  - Booked (current booking count)
  - Active (status badge: Active/Inactive)
  - Actions (Edit, Activate/Deactivate, Delete buttons)

#### Responsive Design
- Horizontally scrollable on small screens
- Clean, modern styling with hover effects
- Status badges with color coding (green=Active, red=Inactive)
- Buttons with distinct colors (blue=Edit, orange=Toggle, red=Delete)

#### JavaScript Event Handlers
Added three interactive handlers:
1. **Delete Button** - Confirms deletion, calls API, reloads on success
2. **Activate/Deactivate Button** - Toggles state without page reload, updates UI in-place
3. **Edit Button** - Multi-prompt interface for editing slot properties:
   - Subject (text input)
   - Capacity (numeric)
   - Start Time (HH:mm format)
   - End Time (HH:mm format)

### 5. Database Migration
**File:** `app/migrations/0014_unlockslot_capacity_unlockslot_end_time_and_more.py`
- Successfully created and applied
- Adds 4 new fields to UnlockSlot table
- Backwards compatible with existing data

## Features Enabled

✅ **Delete Slots** - Remove unlock slots with confirmation dialog
✅ **Edit Slots** - Update subject, times, and capacity with validation
✅ **Toggle Activation** - Disable/enable slots without deletion
✅ **Subject Assignment** - Assign specific subjects to slots
✅ **Time Slot Management** - Define start/end times for each slot
✅ **Capacity Management** - Set booking limits per slot
✅ **Bulk Operations** - Delete multiple slots efficiently (API ready)
✅ **In-Place Updates** - Activate/deactivate without page reload

## Integration Points

### Download Attendance Sheet
The capacity information can be used by attendance sheet generation to:
- Validate if number of students exceeds capacity
- Show capacity warnings
- Flag over-capacity situations

### Calendar Date Publishing
When publishing dates from the calendar, the fields prepare the new endpoint enhancement:
- Can specify subject during publication
- Can set times and capacity during publication (requires additional UI enhancement)

## User Workflow

### Managing Existing Slots
1. Navigate to Admin Dashboard → Calendar/Unlock Dates section
2. View "Existing Slots" table with all details
3. **Edit:** Click "Edit" → modify subject/times/capacity → confirm
4. **Toggle:** Click "Deactivate/Activate" → immediate status change
5. **Delete:** Click "Delete" → confirm deletion → slot removed with bookings

### Capacity Management
1. Edit a slot to set capacity limit
2. System tracks bookings vs capacity
3. Faculty can see available slots before booking

## Security

- All endpoints require admin/staff authentication
- CSRF protection on all POST operations
- Input validation and sanitization
- Error handling with informative messages

## Testing Recommendations

1. **Delete Operation**
   - Create slot → Delete → Verify removed from table
   - Verify associated bookings are cascaded

2. **Edit Operation**
   - Create slot → Edit with new subject/times/capacity
   - Verify updates display in table

3. **Toggle Operation**
   - Edit slot → Click Deactivate → Verify status changes instantly
   - Click Activate → Verify reactivation

4. **Capacity Validation**
   - Set capacity on slot
   - Attempt to exceed during booking
   - Verify behavior (warning or limit)

## Future Enhancements

- Bulk edit functionality (update multiple slots at once)
- Subject/time/capacity input during calendar date publication
- Capacity warning on attendance sheet downloads
- Slot booking analytics dashboard
- Scheduled auto-deactivation of past dates

## Database Impact

Migration 0014 added:
- `subject` column (varchar, nullable)
- `start_time` column (time, nullable)
- `end_time` column (time, nullable)
- `capacity` column (integer, default=0)

All existing slots maintain compatibility with NULL values for new fields.
