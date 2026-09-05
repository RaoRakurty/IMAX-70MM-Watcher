window.QUESTION_BANK = window.QUESTION_BANK || [];
window.QUESTION_BANK.push(
{
  "id":"A18","topic":"Algebra & Functions","cognitive":"routine","type":"choice",
  "stem":"The graph of y = f(x) is translated 3 units to the left and 2 units downward. Which equation represents the transformed graph?",
  "choices":["y = f(x − 3) + 2","y = f(x + 3) − 2","y = f(x − 3) − 2","y = f(x + 3) + 2"],
  "answer":1,"explanation":"A left shift by 3 replaces x with x + 3. A downward shift by 2 subtracts 2 outside the function.","stimulusHtml":""
},
{
  "id":"A19","topic":"Counting & Probability","cognitive":"routine","type":"choice",
  "stem":"At a conference, 18 people are in a room. Each person shakes hands exactly once with every other person. How many different handshakes occur?",
  "choices":["144","153","162","306"],
  "answer":1,"explanation":"The number of unordered pairs is C(18,2) = 18·17/2 = 153.","stimulusHtml":""
},
{
  "id":"A20","topic":"Algebra & Functions","cognitive":"nonroutine","type":"choice",
  "stem":"What is the domain of f(x) = √(x + 4)/(x − 2)?",
  "choices":["[-4,2) ∪ (2,∞)","(-4,2) ∪ (2,∞)","[-4,∞)","(2,∞)"],
  "answer":0,"explanation":"The square root requires x ≥ −4, and the denominator excludes x = 2. Thus the domain is [-4,2) ∪ (2,∞).","stimulusHtml":""
},
{
  "id":"A21","topic":"Data Analysis & Statistics","cognitive":"nonroutine","type":"choice",
  "stem":"Arrange the data sets by standard deviation, from smallest to largest: I. {100,104,104,104,108}; II. {1000,1002,1004,1006,1008}; III. {20,20,20,30,30}.",
  "choices":["I, II, III","II, I, III","III, I, II","I, III, II"],
  "answer":0,"explanation":"Their approximate population standard deviations are 2.53, 2.83, and 4.90, respectively. Therefore I < II < III.","stimulusHtml":""
},
{
  "id":"A22","topic":"Geometry","cognitive":"routine","type":"choice",
  "stem":"An obtuse triangle has a base of 17 units. The perpendicular distance from the opposite vertex to the line containing the base is 8 units, and the altitude falls outside the triangle. What is the area?",
  "choices":["34 square units","68 square units","136 square units","272 square units"],
  "answer":1,"explanation":"The area formula still uses the perpendicular height even when the altitude falls outside: 1/2(17)(8) = 68.","stimulusHtml":""
},
{
  "id":"A23","topic":"Numbers","cognitive":"nonroutine","type":"choice",
  "stem":"Suppose $1 = 0.81 euros and 1 liter = 0.264 gallon. If gasoline costs $4.00 per gallon, approximately what is the price in euros per liter?",
  "choices":["€0.33 per liter","€0.86 per liter","€1.31 per liter","€3.07 per liter"],
  "answer":1,"explanation":"$4/gal × 0.81 euro/$ × 0.264 gal/L = 0.85536 euro/L, about €0.86 per liter.","stimulusHtml":""
},
{
  "id":"N01","topic":"Counting & Probability","cognitive":"nonroutine","type":"choice",
  "stem":"A bag contains 6 red marbles and 4 blue marbles. Two marbles are selected at random without replacement. What is the probability that exactly one of the two marbles is red?",
  "choices":["4/15","8/15","3/5","2/3"],
  "answer":1,"explanation":"Exactly one red can occur as red-blue or blue-red: (6/10)(4/9) + (4/10)(6/9) = 48/90 = 8/15.","stimulusHtml":""
},
{
  "id":"N02","topic":"Algebra & Functions","cognitive":"nonroutine","type":"choice",
  "stem":"What is the coefficient of x⁴ in the expansion of (x − 2)⁶?",
  "choices":["15","30","60","120"],
  "answer":2,"explanation":"The x⁴ term uses C(6,4)x⁴(−2)². Its coefficient is 15·4 = 60.","stimulusHtml":""
},
{
  "id":"N03","topic":"Algebra & Functions","cognitive":"nonroutine","type":"choice",
  "stem":"If log₂(x − 1) + log₂(x − 5) = 4, what is the value of x?",
  "choices":["3 − 2√5","3 + 2√5","6","8"],
  "answer":1,"explanation":"Combine logs: (x−1)(x−5)=16. Then x²−6x−11=0, giving x=3±2√5. The log domain requires x>5, so x=3+2√5.","stimulusHtml":""
},
{
  "id":"N04","topic":"Counting & Probability","cognitive":"nonroutine","type":"choice",
  "stem":"A committee of 5 people is selected from 7 women and 6 men. If the committee must contain exactly 2 women and 3 men, how many different committees are possible?",
  "choices":["210","350","420","840"],
  "answer":2,"explanation":"Choose 2 of the 7 women and 3 of the 6 men: C(7,2)·C(6,3) = 21·20 = 420.","stimulusHtml":""
}
);
