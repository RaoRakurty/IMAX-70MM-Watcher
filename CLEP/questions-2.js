window.QUESTION_BANK = window.QUESTION_BANK || [];
window.QUESTION_BANK.push(
{
  "id":"U11","topic":"Data Analysis & Statistics","cognitive":"routine","type":"choice",
  "stem":"A highway study of 15,000 vehicles found that speeds were approximately normally distributed with a mean of 59 mph and a standard deviation of 6 mph. Approximately how many vehicles had speeds greater than 65 mph?",
  "choices":["375","2,400","5,100","9,900"],
  "answer":1,"explanation":"65 mph is 1 standard deviation above the mean. About 16% of a normal distribution lies above +1 standard deviation. 0.16(15,000) ≈ 2,400.","stimulusHtml":""
},
{
  "id":"U12","topic":"Financial Mathematics","cognitive":"nonroutine","type":"choice",
  "stem":"You win $2 million in the lottery. You invest $1 million in Bank M at 3.02% interest compounded daily and $1 million in Bank N at 3.05% interest compounded quarterly. What is the approximate difference between the interest earned after the first year?",
  "choices":["$0","$192","$264","$300"],
  "answer":1,"explanation":"Bank M earns about $30,659 and Bank N about $30,851 during the first year, a difference of about $191, closest to $192.","stimulusHtml":""
},
{
  "id":"U13","topic":"Financial Mathematics","cognitive":"nonroutine","type":"numeric",
  "stem":"The future value of an investment 75 years from now will be $75,000. If the money earns 5% annual interest compounded semiannually, what is the present value, rounded to the nearest dollar?",
  "answer":1847,"tolerance":1,"suffix":"dollars","explanation":"PV = 75,000/(1 + 0.05/2)^(75·2) ≈ $1,847.","stimulusHtml":""
},
{
  "id":"U14","topic":"Numbers","cognitive":"routine","type":"choice",
  "stem":"Consider the six numbers π, √64, √12, 0.454545…, 7/9, and e. How many of these numbers are irrational?",
  "choices":["1","2","3","4"],
  "answer":2,"explanation":"π, √12, and e are irrational. √64 = 8, a repeating decimal, and 7/9 are rational, so there are 3 irrational numbers.","stimulusHtml":""
},
{
  "id":"U15","topic":"Geometry","cognitive":"nonroutine","type":"choice",
  "stem":"A right isosceles triangle is inscribed in a semicircle so that its hypotenuse is the diameter. The hypotenuse is 4 units long. The part of the semicircle outside the triangle is shaded. What is the area of the shaded region?",
  "choices":["2π − 2","2π − 4","4π − 4","4π − 8"],
  "answer":1,"explanation":"The semicircle has radius 2, so its area is 2π. The isosceles right triangle has legs 2√2, so its area is 1/2(2√2)^2 = 4. Shaded area = 2π − 4.","stimulusHtml":""
},
{
  "id":"U16","topic":"Geometry","cognitive":"routine","type":"choice",
  "stem":"At each vertex of a triangle, one side is extended to form an exterior angle. If the three exterior angles are a, b, and c, what is a + b + c?",
  "choices":["180°","2a","360°","720°"],
  "answer":2,"explanation":"The sum of one exterior angle at each vertex of any convex polygon is 360°. In particular, a + b + c = 360°.","stimulusHtml":""
},
{
  "id":"U17","topic":"Numbers","cognitive":"routine","type":"choice",
  "stem":"Write the value of (6.4 × 10⁻⁴)/(8 × 10⁻⁷) in standard notation.",
  "choices":["0.8","8","80","800"],
  "answer":3,"explanation":"(6.4/8)×10^(−4−(−7)) = 0.8×10³ = 800.","stimulusHtml":""
},
{
  "id":"U18","topic":"Algebra & Functions","cognitive":"routine","type":"choice",
  "stem":"The graph of y = f(x) is translated 2 units to the right and 3 units upward. Which equation represents the transformed graph?",
  "choices":["y = f(x + 2) + 3","y = f(x − 2) + 3","y = f(x + 2) − 3","y = f(x − 2) − 3"],
  "answer":1,"explanation":"A shift right by 2 replaces x with x − 2. A shift up by 3 adds 3 outside the function.","stimulusHtml":""
},
{
  "id":"U19","topic":"Counting & Probability","cognitive":"routine","type":"choice",
  "stem":"In a room of 20 people, if each person shakes hands exactly once with every other person, how many different handshakes are possible?",
  "choices":["40","190","380","400"],
  "answer":1,"explanation":"Each handshake is an unordered pair of people: C(20,2) = 20·19/2 = 190.","stimulusHtml":""
},
{
  "id":"U20","topic":"Algebra & Functions","cognitive":"nonroutine","type":"choice",
  "stem":"What is the domain of f(x) = √(x − 5)/(x − 7)?",
  "choices":["[5, 7) ∪ (7, ∞)","(5, 7) ∪ (7, ∞)","[5, ∞)","(7, ∞)"],
  "answer":0,"explanation":"The square root requires x ≥ 5, while the denominator requires x ≠ 7. Thus the domain is [5,7) ∪ (7,∞).","stimulusHtml":""
}
);
