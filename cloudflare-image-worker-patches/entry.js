import inner from "./index.js";
import { maskTurnstileEnv, protect } from "./security.js";
export { categoryOk, parseCategories, ReadyLimitDO, ReviewsDO } from "./index.js";
// protect() already verified the single-use token on POST /submit and POST /generate,
// and it masks TURNSTILE_ENABLED before the inner fetch. This wrapper masks again so
// an older protect() that does not mask still cannot spend the token a second time.
// Other paths still see TURNSTILE_ENABLED.
const existing = { ...inner, fetch: (request, env, ctx) => inner.fetch(request, maskTurnstileEnv(request, env), ctx) };
export default protect(existing);
