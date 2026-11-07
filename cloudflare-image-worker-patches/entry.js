import inner, { categoryOk, parseCategories, ReadyLimitDO, ReviewsDO as LiveReviewsDO } from "./index.js";
import { createBackupDO } from "./reviews-backup.js";
import { maskTurnstileEnv, protect } from "./security.js";
export { categoryOk, parseCategories, ReadyLimitDO };
// backupPage exists only after this file is deployed. The captured live class has no export method.
export const ReviewsDO = createBackupDO(LiveReviewsDO);
// protect() already verified the single-use token on POST /submit and POST /generate,
// and it masks TURNSTILE_ENABLED before the inner fetch. This wrapper masks again so
// an older protect() that does not mask still cannot spend the token a second time.
// Other paths still see TURNSTILE_ENABLED. POST /review is not masked.
const existing = { ...inner, fetch: (request, env, ctx) => inner.fetch(request, maskTurnstileEnv(request, env), ctx) };
export default protect(existing);
