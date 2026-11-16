# List Management Dashboard — CRUD + Filters

This version upgrades the existing Flask + MySQL project.

## Included
- Create, read, update and delete records.
- Search by title, description, location, region and status.
- Date filters: all dates, last 7/30/90 days, this month, last month.
- Financial-year filters: FY 2026–27, FY 2025–26, FY 2024–25 (April 1 to March 31).
- Custom date range.
- Dynamic location multi-select filter, populated from records in MySQL.
- Region and status dropdown filters.
- Filters can be combined; Clear all resets them.
- Add/edit form validates required fields; delete asks for confirmation.

## Keep your existing database and password
1. Make a backup of your current project folder.
2. Extract/copy these updated files into your existing project, allowing these files to be replaced:
   - `app.py`
   - `templates/index.html`
   - `static/css/style.css`
   - `static/js/app.js`
   - `README.md`
3. **Do not replace or delete your existing `.env` file.** It contains your local MySQL password. This update does not need a new password or database reset.
4. Do not run `schema.sql` again just for this update. The existing `records` table already has the columns this code uses.

## Run
In VS Code terminal, from the project folder:
```bash
python app.py
```
Open http://127.0.0.1:5000

## API endpoints
- `GET /api/health`
- `GET /api/options`
- `GET /api/records` (supports `search`, `date`, `start_date`, `end_date`, `region`, `status`, repeated `location`)
- `POST /api/records`
- `PUT /api/records/<id>`
- `DELETE /api/records/<id>`

## Notes
- The financial-year choices are fixed to the years requested in the project requirements. Update the `fy_map` in `app.py` when you want additional years.
- This uses the current proposed `records` table (`record_title`, `description`, `location`, `region`, `status`, timestamps). It does not claim to reproduce unreadable database column names from the original reference screenshots.
