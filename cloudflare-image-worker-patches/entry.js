import inner from "./index.js";
import { protect } from "./security.js";
export { categoryOk, parseCategories, ReadyLimitDO, ReviewsDO } from "./index.js";
// protect() already verified the single-use Turnstile token; stop the inner /generate from re-verifying it.
const innerEnv = (env) => new Proxy(env, { get: (t, k) => (k === "TURNSTILE_ENABLED" ? "false" : t[k]) });
const existing = { ...inner, fetch: (request, env, ctx) => inner.fetch(request, innerEnv(env), ctx) };
export default protect(existing);
