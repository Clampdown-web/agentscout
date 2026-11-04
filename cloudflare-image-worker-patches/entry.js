import inner from "./index.js";
import { maskTurnstileEnv, protect } from "./security.js";
export { categoryOk, parseCategories, ReadyLimitDO, ReviewsDO } from "./index.js";
// protect() already verified the single-use token on POST /submit and POST /generate.
// maskTurnstileEnv hides the flag on those two paths only, so the inner handler
// does not spend the token again. Other paths still see TURNSTILE_ENABLED.
const existing = { ...inner, fetch: (request, env, ctx) => inner.fetch(request, maskTurnstileEnv(request, env), ctx) };
export default protect(existing);
