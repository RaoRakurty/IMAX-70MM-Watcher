window.QUESTION_BANK = window.QUESTION_BANK || [];
window.QUESTION_BANK.push(
{
  "id":"U01","topic":"Logic & Sets","cognitive":"nonroutine","type":"choice",
  "stem":"Let L = {1, 2, 3, 4}, M = {3, 4, 5}, and P = {1, 2, 5}. Which statement is NOT true?",
  "choices":["L ∩ M = {3, 4}","L ∪ P = {1, 2, 3, 4, 5}","M ∩ P = {2, 5}","(L ∪ M) ∩ P = P"],
  "answer":2,"explanation":"M ∩ P contains only elements common to both sets. The only common element is 5, so M ∩ P = {5}.","stimulusHtml":""
},
{
  "id":"U02","topic":"Numbers","cognitive":"routine","type":"choice",
  "stem":"Which of the following values is an irrational number?",
  "choices":["√81 / 3","0.12121212…","√20 / 2","π / π"],
  "answer":2,"explanation":"√20/2 = √5, which is irrational. The repeating decimal and the other two expressions are rational.","stimulusHtml":""
},
{
  "id":"U03","topic":"Geometry","cognitive":"routine","type":"choice",
  "stem":"In triangle ABC, point X lies on side BC and BX = XC. Segment AX is drawn. What is segment AX?",
  "choices":["Altitude","Median","Angle bisector","Midline"],
  "answer":1,"explanation":"A median joins a vertex to the midpoint of the opposite side. Since BX = XC, X is the midpoint of BC.","stimulusHtml":""
},
{
  "id":"U04","topic":"Logic & Sets","cognitive":"routine","type":"choice",
  "stem":"Which statement is the converse of: If an animal does not eat meat, then the animal is not a carnivore?",
  "choices":["If an animal eats meat, then it is a carnivore.","If an animal is a carnivore, then it eats meat.","If an animal is not a carnivore, then it does not eat meat.","If an animal is a carnivore, then it does not eat meat."],
  "answer":2,"explanation":"The converse of p → q is q → p. Here p is 'does not eat meat' and q is 'is not a carnivore.'","stimulusHtml":""
},
{
  "id":"U05","topic":"Financial Mathematics","cognitive":"nonroutine","type":"choice",
  "stem":"Which investment gives the greatest amount after 5 years on an initial investment of $1,000?",
  "choices":["3.5% APR compounded annually","3.4% APR compounded daily","3.3% APR compounded continuously","3.8% simple interest"],
  "answer":3,"explanation":"The approximate ending values are $1,187.69, $1,185.30, $1,179.39, and $1,190.00. The 3.8% simple-interest option is largest.","stimulusHtml":""
},
{
  "id":"U06","topic":"Data Analysis & Statistics","cognitive":"nonroutine","type":"choice",
  "stem":"A scatterplot has a strong positive linear association, with most points near y = x for x-values from 2 through 6. A new point (1, 5) is added. How would the association and regression line most likely be affected?",
  "choices":["Stronger association and steeper slope","Weaker association and steeper slope","Stronger association and shallower slope","Weaker association and shallower slope"],
  "answer":3,"explanation":"The new point lies well above the existing pattern at a small x-value. It weakens the association and pulls the left end of the fitted line upward, making the positive slope shallower.","stimulusHtml":""
},
{
  "id":"U07","topic":"Algebra & Functions","cognitive":"routine","type":"choice",
  "stem":"For which function does reflecting its graph about the y-axis produce the same graph?",
  "choices":["f(x) = x⁴ + 2x²","f(x) = x³ + 2","f(x) = x² + x","f(x) = |x − 2|"],
  "answer":0,"explanation":"A graph is unchanged by reflection about the y-axis when f(−x) = f(x). x⁴ + 2x² is an even function.","stimulusHtml":""
},
{
  "id":"U08","topic":"Data Analysis & Statistics","cognitive":"routine","type":"choice",
  "stem":"For which type of distribution is the mean generally less than the median?",
  "choices":["Symmetric bell-shaped","Long tail to the left","Long tail to the right","Uniform"],
  "answer":1,"explanation":"In a left-skewed distribution, low extreme values pull the mean toward the left, typically below the median.","stimulusHtml":""
},
{
  "id":"U09","topic":"Logic & Sets","cognitive":"nonroutine","type":"choice",
  "stem":"Let P be true, Q be false, and R be false. Which statement is true?",
  "choices":["(P and R) or Q","(P implies Q) and not R","not P or (Q and R)","not P implies (Q and R)"],
  "answer":3,"explanation":"not P is false. A conditional with a false hypothesis is true, so (not P) → (Q and R) is true.","stimulusHtml":""
},
{
  "id":"U10","topic":"Logic & Sets","cognitive":"routine","type":"choice",
  "stem":"Not counting the empty set, how many proper subsets are there for R = {2, 3, 4}?",
  "choices":["5","6","7","8"],
  "answer":1,"explanation":"A 3-element set has 2³ = 8 subsets. Excluding the empty set and the set itself leaves 6 proper nonempty subsets.","stimulusHtml":""
}
);
