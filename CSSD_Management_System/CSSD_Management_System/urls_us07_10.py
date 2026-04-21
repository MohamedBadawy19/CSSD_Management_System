"""
=======================================================================
  urls_us07_10.py — URL Routes for US-07 to US-10
  Author : Mohamed Badawy
  Sprint : 2

  Registers all URL patterns for the state-transition views and the
  two supporting pages implemented for US-07 through US-10.

  This file is included into the main urls.py via:
      path('', include('CSSD_Management_System.urls_us07_10')),
=======================================================================
"""

from django.urls import path
from . import views_us07_10 as v

urlpatterns = [

    # ── US-07: Mark Instrument as Collected ──────────────────────
    path(
        'requests/<int:request_id>/mark_collected/',
        v.mark_collected,
        name='mark_collected',
    ),

    # ── US-08: Mark Instrument as Cleaned ────────────────────────
    path(
        'requests/<int:request_id>/mark_cleaned/',
        v.mark_cleaned,
        name='mark_cleaned',
    ),

    # ── US-09: Mark Instrument as Sterilized ─────────────────────
    path(
        'requests/<int:request_id>/mark_sterilized/',
        v.mark_sterilized,
        name='mark_sterilized',
    ),

    # ── US-10: Mark Instrument as Packed ─────────────────────────
    path(
        'requests/<int:request_id>/mark_packed/',
        v.mark_packed,
        name='mark_packed',
    ),

    # ── Supporting: CSSD request-details page (Django-rendered) ──
    path(
        'cssd_request_details/<int:request_id>/',
        v.cssd_request_details,
        name='cssd_request_details',
    ),

    # ── Supporting: Nurse sterile-stock page (US-10 AC 2) ────────
    path(
        'nurse_sterile_stock/',
        v.nurse_sterile_stock,
        name='nurse_sterile_stock',
    ),
]
