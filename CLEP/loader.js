(function(){
  const parts = window.__clepParts || [];
  try {
    (0, eval)(parts.join(''));
  } catch (err) {
    const app = document.getElementById('app');
    if (app) app.innerHTML = '<section style="padding:24px;font-family:system-ui"><h1>Exam failed to load</h1><p>Please refresh the page. If the problem continues, contact the exam administrator.</p></section>';
    console.error(err);
  }
})();
