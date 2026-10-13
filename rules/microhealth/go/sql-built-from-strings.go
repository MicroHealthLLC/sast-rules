package main

import (
	"context"
	"database/sql"
	"fmt"
)

func q(ctx context.Context, db *sql.DB, name, label string) {
	// ruleid: go.sql-built-from-strings
	db.Query("SELECT * FROM users WHERE name = '" + name + "'")
	// ruleid: go.sql-built-from-strings
	db.ExecContext(ctx, fmt.Sprintf("DELETE FROM %s", name))
	stmt := "UPDATE t SET a = " + name
	// ruleid: go.sql-built-from-strings
	db.Exec(stmt)
	// ok: go.sql-built-from-strings
	db.Query("SELECT * FROM users WHERE name = $1", name)
	// ok: go.sql-built-from-strings
	runner.Exec(ctx, "launchctl", "bootout", "system/"+label)
	// ok: go.sql-built-from-strings
	db.Exec("SELECT " + "1")
}
