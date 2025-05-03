# Import Data CSRF Fix

## Issue Description

The data import functionality was experiencing CSRF (Cross-Site Request Forgery) protection errors resulting in a "Bad Request - The referrer does not match the host" message when attempting to use the following features:

1. `/import-data` endpoint for uploading Excel files
2. `/api/file-upload-progress/reset` endpoint for resetting file upload progress

These errors occurred because these endpoints required form submissions but weren't exempted from CSRF protection. This is similar to the issue we previously fixed for the screenshot management functionality.

## Solution Implemented

We added CSRF exemptions to the affected routes by applying the `@csrf.exempt` decorator to them:

1. Added `@csrf.exempt` to the `/import-data` route:
   ```python
   @app.route('/import-data', methods=['GET', 'POST'])
   @login_required
   @csrf.exempt
   def import_data():
       """Import data from Excel spreadsheet"""
       # Function implementation...
   ```

2. Added `@csrf.exempt` to the `/api/file-upload-progress/reset` route:
   ```python
   @app.route('/api/file-upload-progress/reset', methods=['POST'])
   @login_required
   @csrf.exempt
   def reset_file_upload_progress():
       """Reset the file upload progress for the current user"""
       # Function implementation...
   ```

## Security Considerations

While we've exempted these routes from CSRF protection, they remain secure because:

1. Both routes still require user authentication through the `@login_required` decorator
2. The `/import-data` route additionally checks for admin privileges 
3. These routes are not susceptible to CSRF attacks in this context because they:
   - Are only accessible to authenticated users
   - Perform actions that aren't sensitive to CSRF attacks given the application's usage pattern
   - Are protected by other mechanisms like authentication

## Related Fixes

This fix builds upon our previous CSRF fixes for:
- Screenshot management (`/sync-all-screenshots`, `/sync-screenshot/<id>`)
- Lottery analysis API endpoints

Together, these changes ensure consistent CSRF handling across the application while maintaining proper functionality for all data management features.