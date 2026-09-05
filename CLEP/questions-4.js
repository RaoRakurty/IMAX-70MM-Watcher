window.QUESTION_BANK = window.QUESTION_BANK || [];
window.QUESTION_BANK.push(
{
  "id":"A08","topic":"Data Analysis & Statistics","cognitive":"routine","type":"choice",
  "stem":"Which type of distribution would generally have mean < median?",
  "choices":["A symmetric bell-shaped distribution","A distribution with a long tail extending to the left","A distribution with a long tail extending to the right","A perfectly uniform distribution"],
  "answer":1,"explanation":"A long left tail pulls the mean downward, so for a negatively skewed distribution the mean is generally less than the median.","stimulusHtml":""
},
{
  "id":"A09","topic":"Logic & Sets","cognitive":"nonroutine","type":"choice",
  "stem":"Let P be false, Q be true, and R be false. Which statement is true?",
  "choices":["(P or R) and Q","(not P) and (Q or R)","(Q implies P) or R","Q and (P or R)"],
  "answer":1,"explanation":"not P is true and Q or R is true, so their conjunction is true.","stimulusHtml":""
},
{
  "id":"A10","topic":"Logic & Sets","cognitive":"routine","type":"choice",
  "stem":"Let S = {a,b,c,d}. Not counting the empty set, how many proper subsets does S have?",
  "choices":["12","13","14","15"],
  "answer":2,"explanation":"A 4-element set has 2⁴ = 16 subsets. Excluding the empty set and S itself leaves 14 proper nonempty subsets.","stimulusHtml":""
},
{
  "id":"A11","topic":"Data Analysis & Statistics","cognitive":"routine","type":"choice",
  "stem":"The speeds of 12,500 vehicles are approximately normally distributed with a mean of 72 mph and a standard deviation of 4 mph. Approximately how many vehicles were traveling faster than 76 mph?",
  "choices":["625","2,000","4,250","6,250"],
  "answer":1,"explanation":"76 mph is 1 standard deviation above the mean. About 16% of a normal distribution lies above +1 standard deviation. 0.16(12,500) ≈ 2,000.","stimulusHtml":""
},
{
  "id":"A12","topic":"Financial Mathematics","cognitive":"nonroutine","type":"choice",
  "stem":"A person invests $1.6 million equally between two banks. Bank A pays 3.20% annual interest compounded daily. Bank B pays 3.24% annual interest compounded quarterly. Approximately how much more interest will the better-performing account earn during the first year?",
  "choices":["$0","$224","$480","$1,920"],
  "answer":1,"explanation":"Each account receives $800,000. The first-year balances differ by about $223.79, so the closest choice is $224.","stimulusHtml":""
},
{
  "id":"A13","topic":"Financial Mathematics","cognitive":"nonroutine","type":"numeric",
  "stem":"An investment will be worth $100,000 in 60 years. If it earns 4.8% annual interest compounded quarterly, approximately what amount must be invested today? Round to the nearest dollar.",
  "answer":5711,"tolerance":1,"suffix":"dollars","explanation":"PV = 100,000/(1 + 0.048/4)^(60·4) ≈ $5,710.54, which rounds to $5,711.","stimulusHtml":""
},
{
  "id":"A14","topic":"Numbers","cognitive":"routine","type":"choice",
  "stem":"Consider the six numbers π, √49, √18, 0.272727…, 11/4, and e. How many are irrational?",
  "choices":["1","2","3","4"],
  "answer":2,"explanation":"π, √18, and e are irrational. √49, the repeating decimal, and 11/4 are rational, so the answer is 3.","stimulusHtml":""
},
{
  "id":"A15","topic":"Geometry","cognitive":"nonroutine","type":"choice",
  "stem":"A right isosceles triangle is inscribed in a semicircle so that its hypotenuse is the diameter. The hypotenuse has length 8. The portion of the semicircle outside the triangle is shaded. What is the shaded area?",
  "choices":["8π − 8","8π − 16","16π − 16","16π − 32"],
  "answer":1,"explanation":"The semicircle has radius 4 and area 8π. The isosceles right triangle has legs 4√2 and area 16. Shaded area = 8π − 16.","stimulusHtml":""
},
{
  "id":"A16","topic":"Geometry","cognitive":"routine","type":"choice",
  "stem":"One exterior angle is formed at each vertex of a triangle. If the three exterior angles are a, b, and c, what is a + b + c?",
  "choices":["90°","180°","360°","540°"],
  "answer":2,"explanation":"The sum of one exterior angle at each vertex of any convex polygon is 360°.","stimulusHtml":""
},
{
  "id":"A17","topic":"Numbers","cognitive":"routine","type":"choice",
  "stem":"Write the value of (4.8 × 10⁻³)/(1.2 × 10⁻⁵) in standard notation.",
  "choices":["4","40","400","4,000"],
  "answer":2,"explanation":"4.8/1.2 = 4 and 10^(−3−(−5)) = 10², so the value is 4×100 = 400.","stimulusHtml":""
}
);
