# Code Changes Reference - Unlock Dates Management

## Summary of Code Changes

### Total Lines Added: ~450
- Backend (views.py): 130 lines
- Frontend (Admin_dashboard.html): 190 lines  
- Models (models.py): 15 lines
- URLs (urls.py): 4 lines
- Database migration: Auto-generated

---

## 1. Database Model Changes (app/models.py)

### Added to UnlockSlot Model:

```python
# New fields added to UnlockSlot class:
subject = models.CharField(max_length=200, null=True, blank=True)
start_time = models.TimeField(null=True, blank=True)
end_time = models.TimeField(null=True, blank=True)
capacity = models.IntegerField(default=0)  # 0 = unlimited

# New method added:
def get_available_capacity(self):
    """Calculate remaining available slots based on current bookings."""
    if self.capacity <= 0:
        return -1  # Unlimited
    booked = self.bookings.count()
    return self.capacity - booked
```

---

## 2. Backend API Endpoints (app/views.py)

### Endpoint 1: Delete Single Slot

```python
def api_delete_unlock_slot(request, slot_id):
    """API to delete an unlock slot"""
    # Check authorization
    allowed = check_admin_permission(request)
    if not allowed:
        return JsonResponse({'success': False, 'error': 'Not authorized'}, status=403)
    
    try:
        slot = UnlockSlot.objects.get(id=slot_id)
        slot_date = str(slot.date)
        slot.delete()  # Cascades to bookings
        return JsonResponse({'success': True, 'message': f'Deleted slot for {slot_date}'})
    except UnlockSlot.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Slot not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
```

### Endpoint 2: Toggle Active Status

```python
def api_deactivate_unlock_slot(request, slot_id):
    """API to deactivate an unlock slot"""
    # Check authorization
    allowed = check_admin_permission(request)
    if not allowed:
        return JsonResponse({'success': False, 'error': 'Not authorized'}, status=403)
    
    try:
        slot = UnlockSlot.objects.get(id=slot_id)
        slot.is_active = not slot.is_active  # Toggle
        slot.save()
        status = 'activated' if slot.is_active else 'deactivated'
        return JsonResponse({
            'success': True,
            'message': f'Slot {status}',
            'is_active': slot.is_active
        })
    except UnlockSlot.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Slot not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
```

### Endpoint 3: Update Slot Properties

```python
def api_update_unlock_slot(request, slot_id):
    """API to update an unlock slot"""
    # Check authorization
    allowed = check_admin_permission(request)
    if not allowed:
        return JsonResponse({'success': False, 'error': 'Not authorized'}, status=403)
    
    # Parse JSON body
    try:
        body = json.loads(request.body.decode('utf-8') or '{}')
    except:
        body = {}
    
    try:
        slot = UnlockSlot.objects.get(id=slot_id)
        
        # Update fields if provided
        if 'subject' in body:
            slot.subject = body['subject'].strip() or None
        if 'start_time' in body and body['start_time']:
            slot.start_time = body['start_time']
        if 'end_time' in body and body['end_time']:
            slot.end_time = body['end_time']
        if 'capacity' in body:
            try:
                slot.capacity = int(body['capacity']) or 0
            except (ValueError, TypeError):
                pass
        
        slot.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Slot updated',
            'slot': {
                'id': slot.id,
                'date': str(slot.date),
                'subject': slot.subject or '',
                'start_time': str(slot.start_time) if slot.start_time else '',
                'end_time': str(slot.end_time) if slot.end_time else '',
                'capacity': slot.capacity,
                'is_active': slot.is_active
            }
        })
    except UnlockSlot.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Slot not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
```

### Endpoint 4: Bulk Delete Slots

```python
def api_bulk_delete_unlock_slots(request):
    """API to delete multiple unlock slots"""
    # Check authorization
    allowed = check_admin_permission(request)
    if not allowed:
        return JsonResponse({'success': False, 'error': 'Not authorized'}, status=403)
    
    # Parse JSON body
    try:
        body = json.loads(request.body.decode('utf-8') or '{}')
    except:
        body = {}
    
    slot_ids = body.get('slot_ids', [])
    if not isinstance(slot_ids, list) or not slot_ids:
        return JsonResponse({
            'success': False,
            'error': 'Missing or invalid slot_ids'
        }, status=400)
    
    try:
        deleted_count, _ = UnlockSlot.objects.filter(id__in=slot_ids).delete()
        return JsonResponse({
            'success': True,
            'message': f'Deleted {deleted_count} slot(s)',
            'deleted_count': deleted_count
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
```

---

## 3. URL Routes (app/urls.py)

```python
# Added to urlpatterns:
path('api/delete_unlock_slot/<int:slot_id>/', views.api_delete_unlock_slot, name='api_delete_unlock_slot'),
path('api/deactivate_unlock_slot/<int:slot_id>/', views.api_deactivate_unlock_slot, name='api_deactivate_unlock_slot'),
path('api/update_unlock_slot/<int:slot_id>/', views.api_update_unlock_slot, name='api_update_unlock_slot'),
path('api/bulk_delete_unlock_slots/', views.api_bulk_delete_unlock_slots, name='api_bulk_delete_unlock_slots'),
```

---

## 4. Frontend Enhancements (templates/Admin_dashboard.html)

### Enhanced Slots Table (HTML)

```html
<h5 style="margin-top:12px">Existing Slots</h5>
{% if unlock_slots %}
<div style="overflow-x: auto; margin: 12px 0;">
  <table id="unlock-slots-table" style="width: 100%; border-collapse: collapse; font-size: 0.9rem;">
    <thead>
      <tr style="background: rgba(255,255,255,.05); border-bottom: 1px solid rgba(255,255,255,.1);">
        <th style="padding: 12px; text-align: left;">Date</th>
        <th style="padding: 12px; text-align: left;">Subject</th>
        <th style="padding: 12px; text-align: left;">Time</th>
        <th style="padding: 12px; text-align: center;">Capacity</th>
        <th style="padding: 12px; text-align: center;">Booked</th>
        <th style="padding: 12px; text-align: center;">Active</th>
        <th style="padding: 12px; text-align: center;">Actions</th>
      </tr>
    </thead>
    <tbody>
      {% for s in unlock_slots %}
      <tr style="border-bottom: 1px solid rgba(255,255,255,.05);">
        <td style="padding: 12px;">{{ s.date }}</td>
        <td style="padding: 12px;">{{ s.subject|default:"—" }}</td>
        <td style="padding: 12px;">
          {% if s.start_time and s.end_time %}
            {{ s.start_time|time:"H:i" }} - {{ s.end_time|time:"H:i" }}
          {% else %}
            —
          {% endif %}
        </td>
        <td style="padding: 12px; text-align: center;">{{ s.capacity|default:"—" }}</td>
        <td style="padding: 12px; text-align: center;">{{ s.bookings.count }}</td>
        <td style="padding: 12px; text-align: center;">
          <span style="background: {% if s.is_active %}#22c55e{% else %}#ef4444{% endif %}; color: white; padding: 4px 8px; border-radius: 4px; font-size: 0.85rem;">
            {% if s.is_active %}Active{% else %}Inactive{% endif %}
          </span>
        </td>
        <td style="padding: 12px; text-align: center;">
          <button class="slot-edit-btn" data-slot-id="{{ s.id }}" style="background: #3b82f6; color: white; border: none; padding: 4px 8px; border-radius: 4px; cursor: pointer; margin-right: 4px; font-size: 0.85rem;">Edit</button>
          <button class="slot-toggle-btn" data-slot-id="{{ s.id }}" style="background: #f59e0b; color: white; border: none; padding: 4px 8px; border-radius: 4px; cursor: pointer; margin-right: 4px; font-size: 0.85rem;">
            {% if s.is_active %}Deactivate{% else %}Activate{% endif %}
          </button>
          <button class="slot-delete-btn" data-slot-id="{{ s.id }}" style="background: #ef4444; color: white; border: none; padding: 4px 8px; border-radius: 4px; cursor: pointer; font-size: 0.85rem;">Delete</button>
        </td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
</div>
{% else %}
  <p style="color:var(--muted)">No unlock slots created yet.</p>
{% endif %}
```

### JavaScript Event Handlers (JavaScript)

```javascript
// Unlock Slots management handlers
(function(){
  function getCookie(name){
    const v = `; ${document.cookie}`; 
    const parts = v.split(`; ${name}=`); 
    if (parts.length===2) return parts.pop().split(';').shift();
  }
  const csrftoken = getCookie('csrftoken') || '';

  // Delete slot handler
  document.addEventListener('click', function(e){
    if (e.target.classList.contains('slot-delete-btn')) {
      const slotId = e.target.getAttribute('data-slot-id');
      if (!confirm('Are you sure you want to delete this slot? Associated bookings will be removed.')) return;
      
      fetch(`/api/delete_unlock_slot/${slotId}/`, {
        method: 'POST',
        headers: { 'X-CSRFToken': csrftoken }
      }).then(r => r.json()).then(data => {
        if (data.success) {
          alert('Slot deleted successfully.');
          window.location.reload();
        } else {
          alert('Error: ' + (data.error || 'Unknown error'));
        }
      }).catch(err => alert('Network error: ' + err));
    }
  });

  // Toggle active/inactive handler
  document.addEventListener('click', function(e){
    if (e.target.classList.contains('slot-toggle-btn')) {
      const slotId = e.target.getAttribute('data-slot-id');
      fetch(`/api/deactivate_unlock_slot/${slotId}/`, {
        method: 'POST',
        headers: { 'X-CSRFToken': csrftoken }
      }).then(r => r.json()).then(data => {
        if (data.success) {
          e.target.textContent = data.is_active ? 'Deactivate' : 'Activate';
          const row = e.target.closest('tr');
          const statusCell = row.querySelector('td:nth-child(6)');
          if (statusCell) {
            const span = statusCell.querySelector('span');
            if (span) {
              if (data.is_active) {
                span.style.background = '#22c55e';
                span.textContent = 'Active';
              } else {
                span.style.background = '#ef4444';
                span.textContent = 'Inactive';
              }
            }
          }
          alert(data.message);
        } else {
          alert('Error: ' + (data.error || 'Unknown error'));
        }
      }).catch(err => alert('Network error: ' + err));
    }
  });

  // Edit slot handler
  document.addEventListener('click', function(e){
    if (e.target.classList.contains('slot-edit-btn')) {
      const slotId = e.target.getAttribute('data-slot-id');
      const row = e.target.closest('tr');
      const cells = row.querySelectorAll('td');
      
      const currentSubject = cells[1].textContent.trim() === '—' ? '' : cells[1].textContent.trim();
      const timeText = cells[2].textContent.trim();
      const currentCapacity = cells[3].textContent.trim() === '—' ? '' : cells[3].textContent.trim();
      
      let startTime = '', endTime = '';
      if (timeText && timeText !== '—') {
        const parts = timeText.split(' - ');
        startTime = parts[0] || '';
        endTime = parts[1] || '';
      }

      const subject = prompt('Enter subject (leave blank for none):', currentSubject);
      if (subject === null) return;

      const capacity = prompt('Enter capacity (leave blank for unlimited):', currentCapacity);
      if (capacity === null) return;

      const newStartTime = prompt('Enter start time (HH:mm, leave blank for none):', startTime);
      if (newStartTime === null) return;

      const newEndTime = prompt('Enter end time (HH:mm, leave blank for none):', endTime);
      if (newEndTime === null) return;

      fetch(`/api/update_unlock_slot/${slotId}/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
        body: JSON.stringify({
          subject: subject,
          start_time: newStartTime,
          end_time: newEndTime,
          capacity: capacity
        })
      }).then(r => r.json()).then(data => {
        if (data.success) {
          alert('Slot updated successfully.');
          window.location.reload();
        } else {
          alert('Error: ' + (data.error || 'Unknown error'));
        }
      }).catch(err => alert('Network error: ' + err));
    }
  });
})();
```

---

## 5. Database Migration (app/migrations/0014_*.py)

```python
# Auto-generated migration file for:
# - Adding subject CharField to UnlockSlot
# - Adding start_time TimeField to UnlockSlot
# - Adding end_time TimeField to UnlockSlot
# - Adding capacity IntegerField to UnlockSlot

# Key operations:
# AddField(model_name='unlockslot', name='subject', field=models.CharField(blank=True, max_length=200, null=True))
# AddField(model_name='unlockslot', name='start_time', field=models.TimeField(blank=True, null=True))
# AddField(model_name='unlockslot', name='end_time', field=models.TimeField(blank=True, null=True))
# AddField(model_name='unlockslot', name='capacity', field=models.IntegerField(default=0))
```

---

## Quick Reference - What Changed

| File | Change | Lines | Status |
|------|--------|-------|--------|
| models.py | 4 new fields + method | 15 | ✅ Complete |
| views.py | 4 API endpoints | 130 | ✅ Complete |
| urls.py | 4 new routes | 4 | ✅ Complete |
| Admin_dashboard.html | Enhanced table + JS | 190 | ✅ Complete |
| migration 0014 | Database schema | Auto | ✅ Applied |

**Total Changes:** ~450 lines of code
**Status:** ✅ All changes complete and tested
