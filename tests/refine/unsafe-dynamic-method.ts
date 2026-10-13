// Fixture for the unsafe-dynamic-method refinement; never executed.
declare const client: any;

export const run = async (method: "queryObject" | "queryArray", args: unknown[]) => {
  // ok: mh.opengrep.javascript.lang.security.audit.unsafe-dynamic-method.unsafe-dynamic-method
  return await (client as any)[method](...args);
};

export function call(name: string, args: unknown[]) {
  // ruleid: mh.opengrep.javascript.lang.security.audit.unsafe-dynamic-method.unsafe-dynamic-method
  return client[name](...args);
}
