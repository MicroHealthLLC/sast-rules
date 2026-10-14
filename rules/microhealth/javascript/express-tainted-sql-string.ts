// License: MIT (c) MicroHealth, LLC. Rule-test fixture for javascript.express-tainted-sql-string; never executed.
declare const db: { query(q: string): Promise<unknown> };
declare const logger: { error(...a: unknown[]): void };
declare function logError(fn: string, msg: string): void;

export async function handler(req: any, res: any) {
  const errorText = req.body.message;
  const id = req.query.id;
  // ruleid: javascript.express-tainted-sql-string
  await db.query(`SELECT * FROM users WHERE id = ${id}`);
  // ruleid: javascript.express-tainted-sql-string
  const q = "DELETE FROM sessions WHERE token = '" + req.params.token + "'";
  await db.query(q);
  // ok: javascript.express-tainted-sql-string
  logError("fn", `Failed to create upload session: ${errorText}`);
  // ok: javascript.express-tainted-sql-string
  console.warn(`[hook] attachment row insert failed for ${req.body.filename}:`, errorText);
  // ok: javascript.express-tainted-sql-string
  logger.error(`could not update status set by ${req.body.user}`);
  if (!res) {
    // ok: javascript.express-tainted-sql-string
    throw new Error(`Failed to create folder: ${errorText}`);
  }
  // ok: javascript.express-tainted-sql-string
  const err = new Error(`Failed to create sharing link: ${errorText}`);
  res.status(500).send(err.message);
}
