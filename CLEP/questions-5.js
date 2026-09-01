window.QUESTION_BANK = window.QUESTION_BANK || [];
window.QUESTION_BANK.push(
{
  "id": "G1","topic": "Geometry","cognitive": "nonroutine","type": "choice","stem": "Triangle ABC is similar to triangle DEF. A side of ABC corresponding to a side of DEF has lengths 6 and 15, respectively. If the area of triangle ABC is 40 square units, what is the area of triangle DEF?","choices": ["100","160","200","250"],"answer": 3,"explanation": "The side scale factor is 15/6=2.5, so the area scale factor is 2.5²=6.25. Then 40·6.25=250.","stimulusHtml": ""
},
{
  "id": "G2","topic": "Geometry","cognitive": "nonroutine","type": "choice","stem": "A rectangular display has a diagonal of 26 inches. The ratio of its length to its width is 12 to 5. What is the perimeter of the display, in inches?","choices": ["52","60","68","78"],"answer": 2,"explanation": "A 5-12-13 triangle scaled by 2 has sides 10 and 24 with diagonal 26. Perimeter = 2(10+24)=68.","stimulusHtml": ""
},
{
  "id": "G3","topic": "Geometry","cognitive": "nonroutine","type": "choice","stem": "A sector of a circle has a central angle of 72 degrees and an area of 20π square units. What is the radius of the circle?","choices": ["5","8","10","12"],"answer": 2,"explanation": "72° is 1/5 of a circle. Therefore the full circle area is 100π, so r²=100 and r=10.","stimulusHtml": ""
},
{
  "id": "G4","topic": "Geometry","cognitive": "nonroutine","type": "numeric","stem": "A square is inscribed in a circle whose area is 25π square units. What is the area of the square?","answer": 50,"tolerance": 1e-06,"suffix": "","explanation": "The circle has radius 5 and diameter 10. The square's diagonal is 10, so its area is d²/2 = 100/2 = 50.","stimulusHtml": ""
},
{
  "id": "G5","topic": "Geometry","cognitive": "routine","type": "choice","stem": "Each edge of a cube has length 3. What is the length of a space diagonal joining two opposite vertices of the cube?","choices": ["3√2","3√3","6","9"],"answer": 1,"explanation": "The space diagonal of a cube with side s is s√3, so the length is 3√3.","stimulusHtml": ""
},
{
  "id": "G6","topic": "Geometry","cognitive": "routine","type": "numeric","stem": "A circular reservoir has circumference 640π meters. What is the diameter of the reservoir, in meters?","answer": 640,"tolerance": 1e-06,"suffix": "meters","explanation": "Since C=πd, 640π=πd, so d=640.","stimulusHtml": ""
},
{
  "id": "N1","topic": "Numbers","cognitive": "routine","type": "matrix","stem": "Let m = 8 and n = 2. For each expression, indicate whether its value is rational or irrational.","columns": ["Rational","Irrational"],"rows": ["√(m + n)","√m / √n","√(mn)","√m - √n"],"answers": [1,0,0,1],"explanation": "With m=8 and n=2: √10 is irrational; √8/√2=√4=2 is rational; √16=4 is rational; √8-√2=√2 is irrational.","stimulusHtml": ""
},
{
  "id": "N2","topic": "Numbers","cognitive": "nonroutine","type": "matrix","stem": "m is an odd integer. For each expression, indicate whether the value must be odd or even.","columns": ["Odd","Even"],"rows": ["3m + 1","m² + m","m²","2m - 5"],"answers": [1,1,0,0],"explanation": "For odd m: 3m is odd so 3m+1 is even; m(m+1) is even; m² is odd; 2m is even and even-5 is odd.","stimulusHtml": ""
},
{
  "id": "N3","topic": "Numbers","cognitive": "routine","type": "choice","stem": "If (4.8 × 10^7)/(1.2 × 10^-3) = 4 × 10^n, what is the value of n?","choices": ["4","7","10","11"],"answer": 2,"explanation": "4.8/1.2=4 and 10^7/10^-3=10^(7-(-3))=10^10, so n=10.","stimulusHtml": ""
},
{
  "id": "N4","topic": "Numbers","cognitive": "routine","type": "choice","stem": "Which of the following is the prime factorization of 756?","choices": ["2²·3³·7","2³·3²·7","2²·3·7²","2·3³·14"],"answer": 0,"explanation": "756=4·189=2²·3³·7.","stimulusHtml": ""
},
{
  "id": "N5","topic": "Numbers","cognitive": "routine","type": "choice","stem": "A hiking trail is 2.75 miles long. If 1 mile = 5,280 feet, how many feet long is the trail?","choices": ["13,200","14,080","14,520","15,840"],"answer": 2,"explanation": "2.75·5,280 = 14,520 feet.","stimulusHtml": ""
},
{
  "id": "N6","topic": "Numbers","cognitive": "nonroutine","type": "choice","stem": "A length is reported as 12.4 centimeters after being rounded to the nearest tenth of a centimeter. Which of the following describes all possible actual lengths x, in centimeters, that would round to 12.4?","choices": ["12.3 ≤ x < 12.5","12.35 ≤ x < 12.45","12.39 ≤ x ≤ 12.41","12.4 ≤ x < 12.5"],"answer": 1,"explanation": "Values from 12.35 up to but not including 12.45 round to 12.4 to the nearest tenth.","stimulusHtml": ""
}
);
