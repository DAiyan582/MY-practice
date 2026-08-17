# Exam CRUD API Boilerplate (Node.js / Express)

## 1. Run it
```bash
npm install
npm start
# or: npm run dev   (auto-restart with nodemon)
```
Server runs at `http://localhost:5000`.

## 2. Adapting to a different resource in the exam
This boilerplate implements CRUD for `enrollments`. If the exam gives you a
different resource (students, books, products...):

1. Copy `routes/enrollments.js` -> `routes/<resource>.js`
2. Inside the new file, change:
   - `const RESOURCE = 'enrollments'` -> your resource name
   - `REQUIRED_FIELDS` -> the fields that must be present on create
3. Update `data/db.json` to have a top-level array with that same name,
   e.g. `{ "books": [ ... ] }`
4. In `server.js`, mount it:
   ```js
   app.use('/api/<resource>', checkApiKey, require('./routes/<resource>'));
   ```
That's the whole template — the CRUD logic itself never changes.

## 3. Test with curl
```bash
KEY="secret123"

curl http://localhost:5000/api/enrollments \
  -H "X-API-Key: $KEY"

curl "http://localhost:5000/api/enrollments?courseCode=CSE4165&status=enrolled" \
  -H "X-API-Key: $KEY"

curl http://localhost:5000/api/enrollments/1 \
  -H "X-API-Key: $KEY"

curl -X POST http://localhost:5000/api/enrollments \
  -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d '{"studentName":"Sadia Islam","courseCode":"CSE4165","semester":"Fall2026"}'

curl -X PUT http://localhost:5000/api/enrollments/1 \
  -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d '{"status":"dropped"}'

curl -X DELETE http://localhost:5000/api/enrollments/1 \
  -H "X-API-Key: $KEY"

# 401 test (no key)
curl http://localhost:5000/api/enrollments

# 404 test
curl http://localhost:5000/api/enrollments/999 -H "X-API-Key: $KEY"

# 400 test (missing required field)
curl -X POST http://localhost:5000/api/enrollments \
  -H "X-API-Key: $KEY" -H "Content-Type: application/json" -d '{}'
```

## 4. Git workflow (branch-per-question, then merge)
```bash
git init
git add .
git commit -m "Initial commit: project setup"

# for EACH question/operation:
git checkout -b feature/retrieve
# ...implement / edit files...
git add .
git commit -m "Implement GET routes"
git checkout main
git merge feature/retrieve

git checkout -b feature/save
# ...implement POST...
git add .
git commit -m "Implement POST route"
git checkout main
git merge feature/save

# repeat for feature/update, feature/delete, feature/auth, etc.
```

## 5. Status code quick reference
| Code | Meaning                         |
|------|----------------------------------|
| 200  | OK (GET/PUT/DELETE success)      |
| 201  | Created (POST success)           |
| 400  | Bad request / validation error   |
| 401  | Unauthorized (missing/bad key)   |
| 404  | Not found                        |
| 500  | Server error                     |
