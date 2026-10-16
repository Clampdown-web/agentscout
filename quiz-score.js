/* AgentScout quiz scorer. Pure function, no DOM: works in the browser (window.ASQuiz) and in the app (module.exports).
   score(tool, answers, quiz) uses api/quiz.json weights against api/tools.json fields. */
(function (root) {
  function score(t, a, quiz) {
    var W = quiz.weights, s = 0;
    var g = (quiz.questions[0].options || []).filter(function (o) { return o.id === a.goal; })[0];
    if (g) {
      if (g.categories.indexOf(t.category) >= 0) s += W.goal.category;
      if ((t.goals || []).some(function (x) { return g.goals.indexOf(x) >= 0; })) s += W.goal.goals;
      if (!s && W.goal.requireMatch) return -1;
    }
    var sk = t.skill === 'no-code' ? 'no-code' : 'developer';
    if (W.skill[a.skill]) s += W.skill[a.skill][sk] || 0;
    var p = t.price_tag || t.priceTag || 'unknown';
    if (W.budget[a.budget]) s += W.budget[a.budget][p] || 0;
    if (W.oss[a.oss]) s += W.oss[a.oss][t.github ? 'github' : 'none'];
    if (t.weekly_pick || t.weeklyPick) s += W.bonus.weekly_pick;
    if (t.logo) s += W.bonus.logo;
    return s;
  }
  function rank(tools, a, quiz) {
    var max = (quiz.results && quiz.results.max) || 8;
    return tools.map(function (t, i) { return { t: t, s: score(t, a, quiz), i: i }; })
      .filter(function (x) { return x.s > 0; })
      .sort(function (x, y) { return y.s - x.s || x.i - y.i; })
      .slice(0, max).map(function (x) { return x.t; });
  }
  var api = { score: score, rank: rank };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else root.ASQuiz = api;
})(typeof window !== 'undefined' ? window : this);
