window.QUESTION_BANK = window.QUESTION_BANK || [];
window.QUESTION_BANK.push(
{
  "id": "A1",
  "topic": "Algebra & Functions",
  "cognitive": "nonroutine",
  "type": "choice",
  "stem": "A community center had 2,400 members at the beginning of 2023 and 2,940 members at the beginning of 2026. If the number of members increased linearly, which of the following represents the number M of members t years after the beginning of 2023?",
  "choices": ["M = 2,400 + 180t","M = 2,400 + 540t","M = 2,940 + 180t","M = 2,940 + 540(t - 3)"],
  "answer": 0,
  "explanation": "The increase was 540 over 3 years, or 180 per year. Starting at 2,400 gives M = 2,400 + 180t.",
  "stimulusHtml": ""
},
{
  "id": "A2","topic": "Algebra & Functions","cognitive": "routine","type": "choice",
  "stem": "Values of the functions f and g are shown in the tables. What is the value of f(g(4))?",
  "choices": ["1","5","7","9"],"answer": 3,
  "explanation": "From the g table, g(4) = 8. From the f table, f(8) = 9.",
  "stimulusHtml": "\n<div class=\"stimulus-grid two\">\n<table class=\"data-table\"><caption>Function f</caption><thead><tr><th>x</th><th>f(x)</th></tr></thead>\n<tbody><tr><td>2</td><td>5</td></tr><tr><td>4</td><td>7</td></tr><tr><td>6</td><td>1</td></tr><tr><td>8</td><td>9</td></tr></tbody></table>\n<table class=\"data-table\"><caption>Function g</caption><thead><tr><th>x</th><th>g(x)</th></tr></thead>\n<tbody><tr><td>2</td><td>6</td></tr><tr><td>4</td><td>8</td></tr><tr><td>6</td><td>4</td></tr><tr><td>8</td><td>2</td></tr></tbody></table>\n</div>"
},
{
  "id": "A3","topic": "Algebra & Functions","cognitive": "nonroutine","type": "choice",
  "stem": "A researcher recorded the number of cells in a culture at the times shown. Based on the data, which of the following functions best models the number of cells C(t) after t hours?",
  "choices": ["C(t) = 120 + 60t","C(t) = 120(2^t)","C(t) = 120(2^(t/2))","C(t) = 120t² + 2"],"answer": 2,
  "explanation": "The population doubles every 2 hours, so the exponent is t/2: C(t) = 120·2^(t/2).",
  "stimulusHtml": "\n<table class=\"data-table compact\"><caption>Measured population</caption><thead><tr><th>Time t (hours)</th><th>Cells</th></tr></thead>\n<tbody><tr><td>0</td><td>120</td></tr><tr><td>2</td><td>240</td></tr><tr><td>4</td><td>480</td></tr><tr><td>6</td><td>960</td></tr></tbody></table>"
},
{
  "id": "A4","topic": "Algebra & Functions","cognitive": "routine","type": "choice","stem": "The width of a rectangular garden is x feet. If 360 feet of fencing is needed to enclose the garden, which of the following represents the length of the garden, in feet?","choices": ["360 - x","360 - 2x","180 - x","180 - 2x"],"answer": 2,"explanation": "2L + 2x = 360, so L + x = 180 and L = 180 - x.","stimulusHtml": ""
},
{
  "id": "A5","topic": "Algebra & Functions","cognitive": "routine","type": "choice","stem": "Which of the following is the solution to 7(2^x) = 84?","choices": ["x = ln(12)/ln(2)","x = ln(84)/ln(2)","x = ln(77)/ln(2)","x = ln(12) - ln(2)"],"answer": 0,"explanation": "Divide by 7 to get 2^x = 12. Therefore x = log₂12 = ln(12)/ln(2).","stimulusHtml": ""
},
{
  "id": "A6","topic": "Algebra & Functions","cognitive": "routine","type": "choice","stem": "A manufactured part is acceptable if its mass is from 47.4 grams to 48.6 grams, inclusive. Which of the following inequalities describes all acceptable masses x, in grams?","choices": ["|x - 48| ≤ 0.6","|x - 48| ≥ 0.6","|x - 47.4| ≤ 1.2","|x - 48.6| ≤ 0.6"],"answer": 0,"explanation": "The interval is centered at 48 with maximum distance 0.6, so |x - 48| ≤ 0.6.","stimulusHtml": ""
},
{
  "id": "A7","topic": "Algebra & Functions","cognitive": "routine","type": "numeric","stem": "The function f is defined by f(x) = x² + 1 for x < 0 and f(x) = 3x - 2 for x ≥ 0. What is the value of f(-3) + f(4)?","answer": 20,"tolerance": 1e-06,"suffix": "","explanation": "f(-3) = 9 + 1 = 10 and f(4) = 12 - 2 = 10, so the sum is 20.","stimulusHtml": ""
},
{
  "id": "A8","topic": "Algebra & Functions","cognitive": "nonroutine","type": "choice","stem": "The graph of y = f(x) is transformed to obtain the graph of y = f(-x) + 3. Which of the following describes the transformation?","choices": ["Reflect across the x-axis, then shift up 3 units.","Reflect across the y-axis, then shift up 3 units.","Shift left 3 units, then reflect across the y-axis.","Shift right 3 units, then reflect across the x-axis."],"answer": 1,"explanation": "Replacing x by -x reflects the graph across the y-axis. Adding 3 shifts it upward 3 units.","stimulusHtml": ""
},
{
  "id": "A9","topic": "Algebra & Functions","cognitive": "nonroutine","type": "numeric","stem": "The equations x + y = 10, y + z = 15, and z + t = 22 are true. What is the value of x + t?","answer": 17,"tolerance": 1e-06,"suffix": "","explanation": "Add the first and third equations and subtract the second: (x+y)+(z+t)-(y+z)=10+22-15=17.","stimulusHtml": ""
},
{
  "id": "A10","topic": "Algebra & Functions","cognitive": "nonroutine","type": "choice","stem": "Let f(x) = 1/(x - 4) and g(x) = 2x + 4. Which of the following is the domain of the composite function f(g(x))?","choices": ["All real numbers","All real numbers except 0","All real numbers except 2","All real numbers except 4"],"answer": 1,"explanation": "f(g(x)) = 1/[(2x+4)-4] = 1/(2x), so x = 0 must be excluded.","stimulusHtml": ""
},
{
  "id": "A11","topic": "Algebra & Functions","cognitive": "nonroutine","type": "choice","stem": "The cost C, in dollars, of a taxi ride is modeled by C = 4.50 + 2.25m, where m is the number of miles traveled. Which of the following best describes the number 2.25 in this model?","choices": ["The fixed charge before any miles are traveled","The number of miles included in the fixed charge","The increase in cost for each additional mile","The total cost of a 2.25-mile ride"],"answer": 2,"explanation": "The coefficient of m is the rate of change: the fare increases $2.25 per mile.","stimulusHtml": ""
},
{
  "id": "A12","topic": "Algebra & Functions","cognitive": "routine","type": "choice","stem": "Which of the following sets of real numbers is the solution set of |2x - 5| ≤ 7?","choices": ["[-1, 6]","[-6, 1]","(-∞, -1] ∪ [6, ∞)","[-1, 1]"],"answer": 0,"explanation": "-7 ≤ 2x - 5 ≤ 7 gives -2 ≤ 2x ≤ 12, so -1 ≤ x ≤ 6.","stimulusHtml": ""
}
);
