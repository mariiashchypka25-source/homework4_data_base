EXPLAIN ANALYZE 
SELECT * FROM Borrow_Log 
WHERE user_id = 4444;


CREATE INDEX IF NOT EXISTS idx_borrow_log_user_search 
ON Borrow_Log(user_id);
EXPLAIN ANALYZE 
SELECT * FROM Borrow_Log 
WHERE user_id = 4444;