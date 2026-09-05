window.GEOMETRY_QUESTIONS = [
{
 id:"G01",topic:"Triangles",level:"Routine",stem:"In triangle ABC, point D lies on side BC and BD = DC. Segment AD is drawn. Which of the following best describes segment AD?",choices:["Altitude","Median","Angle bisector","Perpendicular bisector"],answer:1,explanation:"Since BD = DC, D is the midpoint of BC. A segment from a vertex to the midpoint of the opposite side is a median.",diagram:{type:"median"}
},
{
 id:"G02",topic:"Triangles",level:"Routine",stem:"In triangle PQR, point S lies on QR and PS is perpendicular to QR. Which of the following best describes segment PS?",choices:["Altitude","Median","Angle bisector","Midsegment"],answer:0,explanation:"An altitude is a perpendicular segment from a vertex to the line containing the opposite side.",diagram:{type:"altitude"}
},
{
 id:"G03",topic:"Triangles",level:"Nonroutine",stem:"In the figure below, one side of triangle ABC is extended through C. If the exterior angle is 128° and angle A measures 47°, what is the measure of angle B?",choices:["47°","72°","81°","128°"],answer:2,explanation:"An exterior angle equals the sum of the two remote interior angles. Thus 128 = 47 + B, so B = 81°.",diagram:{type:"exterior",a:"47°",ext:"128°"}
},
{
 id:"G04",topic:"Triangles",level:"Routine",stem:"The base of the triangle shown is 18 units and its perpendicular height is 11 units. What is the area of the triangle?",choices:["90 square units","99 square units","108 square units","198 square units"],answer:1,explanation:"Area = (1/2)(base)(height) = (1/2)(18)(11) = 99.",diagram:{type:"triangleHeight",base:"18",height:"11"}
},
{
 id:"G05",topic:"Triangles",level:"Routine",stem:"A right triangle has hypotenuse 26 and one leg of length 24. What is the length x of the other leg?",choices:["8","10","12","14"],answer:1,explanation:"By the Pythagorean theorem, x² + 24² = 26², so x² = 100 and x = 10.",diagram:{type:"rightTriangle",a:"24",b:"x",c:"26"}
},
{
 id:"G06",topic:"Circles",level:"Nonroutine",stem:"The figure below shows a sector of a circle. The length of arc AB is 18 units, and the measure of central angle AOB is 45°. What is the area of sector AOB?",choices:["324/π square units","648/π square units","162π square units","324π square units"],answer:1,explanation:"45° = π/4 radians. Since s = rθ, 18 = r(π/4), so r = 72/π. Sector area = (1/2)rs = (1/2)(72/π)(18) = 648/π.",diagram:{type:"sector",angle:"45°",arc:"18"}
},
{
 id:"G07",topic:"Circles",level:"Routine",stem:"A circle has radius 15. What is the length of an arc whose central angle measures 72°?",choices:["3π","6π","12π","30π"],answer:1,explanation:"The arc is 72/360 = 1/5 of the circumference. Its length is (1/5)(2π·15) = 6π.",diagram:{type:"arc",angle:"72°",radius:"15"}
},
{
 id:"G08",topic:"Circles",level:"Routine",stem:"Two concentric circles have radii 10 and 6. What is the area of the shaded region between the circles?",choices:["16π","36π","64π","100π"],answer:2,explanation:"The annulus area is π(10² − 6²) = π(100 − 36) = 64π.",diagram:{type:"annulus",outer:"10",inner:"6"}
},
{
 id:"G09",topic:"Triangles",level:"Nonroutine",stem:"In triangle ABC, AD bisects angle A and meets BC at D. If AB = 12, AC = 18, and BD = 8, what is DC?",choices:["8","10","12","18"],answer:2,explanation:"By the angle-bisector theorem, BD/DC = AB/AC = 12/18 = 2/3. Thus 8/DC = 2/3, giving DC = 12.",diagram:{type:"angleBisector",left:"12",right:"18",bd:"8",dc:"?"}
},
{
 id:"G10",topic:"Similarity",level:"Routine",stem:"The two triangles shown are similar. A side of length 7 in the smaller triangle corresponds to a side of length 21 in the larger triangle. If another side of the smaller triangle has length 10, what is the length x of the corresponding side of the larger triangle?",choices:["21","24","30","35"],answer:2,explanation:"The scale factor is 21/7 = 3. Therefore x = 10(3) = 30.",diagram:{type:"similar",small1:"7",large1:"21",small2:"10",large2:"x"}
},
{
 id:"G11",topic:"Lines & Angles",level:"Nonroutine",stem:"In the figure below, lines l and m are parallel. The marked 68° angle and angle x are same-side interior angles. What is x?",choices:["68°","112°","122°","248°"],answer:1,explanation:"Same-side interior angles formed by a transversal of parallel lines are supplementary. Thus x = 180 − 68 = 112°.",diagram:{type:"parallel",angle:"68°",x:"x"}
},
{
 id:"G12",topic:"Polygons",level:"Routine",stem:"What is the sum of the measures of the interior angles of a hexagon?",choices:["540°","600°","720°","900°"],answer:2,explanation:"For an n-gon, the interior-angle sum is (n − 2)180°. For n = 6, the sum is 4(180) = 720°.",diagram:{type:"hexagon"}
},
{
 id:"G13",topic:"Polygons",level:"Nonroutine",stem:"Each exterior angle of a regular polygon measures 24°. How many sides does the polygon have?",choices:["12","15","18","24"],answer:1,explanation:"The exterior angles of any polygon sum to 360°. For a regular polygon, n = 360/24 = 15.",diagram:{type:"regularPolygon",sides:15,label:"24°"}
},
{
 id:"G14",topic:"Coordinate Geometry",level:"Routine",stem:"What is the distance between the points A(−2, 3) and B(4, 11)?",choices:["8","10","12","14"],answer:1,explanation:"Distance = √[(4−(−2))² + (11−3)²] = √(36+64) = 10.",diagram:{type:"coordinate",points:[[-2,3,"A"],[4,11,"B"]]}
},
{
 id:"G15",topic:"Coordinate Geometry",level:"Routine",stem:"What is the midpoint of the segment with endpoints (−5, 8) and (7, −4)?",choices:["(1, 2)","(2, 1)","(−1, 2)","(1, −2)"],answer:0,explanation:"Average the x-coordinates and y-coordinates: ((−5+7)/2, (8−4)/2) = (1, 2).",diagram:{type:"coordinate",points:[[-5,8,"A"],[7,-4,"B"]]}
},
{
 id:"G16",topic:"Lines & Angles",level:"Nonroutine",stem:"A line passes through (2, −1) and (6, 7). Which of the following is the slope of a line perpendicular to it?",choices:["−2","−1/2","1/2","2"],answer:1,explanation:"The given line has slope (7−(−1))/(6−2) = 8/4 = 2. A perpendicular line has slope −1/2.",diagram:null
},
{
 id:"G17",topic:"Quadrilaterals",level:"Routine",stem:"A rectangle has length 15 and width 8. What is the length of a diagonal of the rectangle?",choices:["16","17","18","23"],answer:1,explanation:"The diagonal is the hypotenuse of a right triangle with legs 15 and 8: d = √(15²+8²) = √289 = 17.",diagram:{type:"rectangleDiagonal",w:"15",h:"8",d:"d"}
},
{
 id:"G18",topic:"Quadrilaterals",level:"Routine",stem:"A trapezoid has parallel bases of lengths 12 and 20 and height 9. What is its area?",choices:["126","144","180","288"],answer:1,explanation:"Area = (1/2)(b₁+b₂)h = (1/2)(12+20)(9) = 144.",diagram:{type:"trapezoid",b1:"12",b2:"20",h:"9"}
},
{
 id:"G19",topic:"Quadrilaterals",level:"Routine",stem:"The diagonals of a rhombus have lengths 10 and 24. What is the area of the rhombus?",choices:["60","100","120","240"],answer:2,explanation:"Area of a rhombus = (1/2)d₁d₂ = (1/2)(10)(24) = 120.",diagram:{type:"rhombus",d1:"10",d2:"24"}
},
{
 id:"G20",topic:"Solid Geometry",level:"Routine",stem:"A right circular cylinder has radius 4 and height 9. What is its volume?",choices:["36π","72π","144π","288π"],answer:2,explanation:"V = πr²h = π(4²)(9) = 144π.",diagram:{type:"cylinder",r:"4",h:"9"}
},
{
 id:"G21",topic:"Solid Geometry",level:"Nonroutine",stem:"A rectangular prism has dimensions 5 by 6 by 8. What is the total surface area of the prism?",choices:["118","188","236","240"],answer:2,explanation:"Surface area = 2(lw+lh+wh) = 2(30+40+48) = 236.",diagram:{type:"prism",a:"5",b:"6",c:"8"}
},
{
 id:"G22",topic:"Solid Geometry",level:"Routine",stem:"A right circular cone has radius 6 and height 10. What is its volume?",choices:["60π","120π","180π","360π"],answer:1,explanation:"V = (1/3)πr²h = (1/3)π(36)(10) = 120π.",diagram:{type:"cone",r:"6",h:"10"}
},
{
 id:"G23",topic:"Composite Figures",level:"Nonroutine",stem:"A circle is inscribed in a square with side length 14. What is the total area inside the square but outside the circle?",choices:["49π","196 − 49π","196 − 14π","196 + 49π"],answer:1,explanation:"The square area is 196. The inscribed circle has radius 7 and area 49π. The required area is 196 − 49π.",diagram:{type:"squareCircle",side:"14"}
},
{
 id:"G24",topic:"Composite Figures",level:"Nonroutine",stem:"A 20-by-14 rectangle contains a semicircle of radius 7 cut from each of its two shorter sides, as shown. The two semicircles do not overlap. What is the area of the remaining region?",choices:["280 − 98π","280 − 49π","140 − 49π","280 + 49π"],answer:1,explanation:"The two semicircles together form one full circle of radius 7, area 49π. Subtract from the rectangle: 280 − 49π.",diagram:{type:"doubleSemi",w:"20",h:"14"}
},
{
 id:"G25",topic:"Composite Figures",level:"Nonroutine",stem:"A figure consists of an 18-by-12 rectangle topped by a triangle with base 18 and height 8. A circular opening of radius 3 is removed from the rectangle. What is the area of the remaining figure?",choices:["216 − 9π","288 − 9π","288 − 18π","360 − 9π"],answer:1,explanation:"Rectangle area = 216; triangle area = 72; circular opening = 9π. Remaining area = 216 + 72 − 9π = 288 − 9π.",diagram:{type:"houseHole",w:"18",rectH:"12",triH:"8",r:"3"}
},
{
 id:"G26",topic:"Composite Figures",level:"Nonroutine",stem:"Inside a square of side 12, a quarter-circle of radius 6 is drawn from each corner. The four quarter-circles do not overlap. What is the area of the region inside the square but outside all four quarter-circles?",choices:["144 − 18π","144 − 36π","72 − 18π","144 − 72π"],answer:1,explanation:"Four quarter-circles of radius 6 have the same total area as one full circle of radius 6: 36π. Subtract from the square area 144 to get 144 − 36π.",diagram:{type:"quarterSquare",side:"12",r:"6"}
},
{
 id:"G27",topic:"Composite Figures",level:"Nonroutine",stem:"A right triangle with legs 6 and 8 is inscribed in a semicircle whose diameter is the triangle's hypotenuse. What is the area of the semicircle outside the triangle?",choices:["25π/2 − 24","25π − 24","50π − 24","25π/2 − 48"],answer:0,explanation:"The hypotenuse is 10, so the semicircle radius is 5. Semicircle area = 25π/2. Triangle area = 24. Difference = 25π/2 − 24.",diagram:{type:"semiTriangle",a:"6",b:"8",d:"10"}
},
{
 id:"G28",topic:"Circles",level:"Nonroutine",stem:"Points A, B, and C lie on a circle. The central angle AOC intercepting arc AC measures 136°. What is the measure of inscribed angle ABC that intercepts the same arc AC?",choices:["34°","68°","136°","272°"],answer:1,explanation:"An inscribed angle equals one-half the measure of the central angle intercepting the same arc. Thus 136/2 = 68°.",diagram:{type:"inscribed",central:"136°",inscribed:"x"}
},
{
 id:"G29",topic:"Circles",level:"Nonroutine",stem:"From external point P, segment PT is tangent to a circle at T. The radius OT is 5 and OP = 13. What is PT?",choices:["5","8","12","18"],answer:2,explanation:"A radius to a tangent is perpendicular at the point of tangency, so OPT is a right triangle. PT = √(13²−5²) = √144 = 12.",diagram:{type:"tangent",r:"5",hyp:"13",tan:"x"}
},
{
 id:"G30",topic:"Polygons",level:"Nonroutine",stem:"How many diagonals can be drawn in a 12-sided polygon?",choices:["44","48","54","66"],answer:2,explanation:"The number of diagonals in an n-gon is n(n−3)/2. For n = 12: 12·9/2 = 54.",diagram:{type:"polygon12"}
},
{
 id:"G31",topic:"Similarity",level:"Nonroutine",stem:"Two similar figures have corresponding side lengths in the ratio 3:5. If the area of the smaller figure is 54 square units, what is the area of the larger figure?",choices:["90","120","150","250"],answer:2,explanation:"Areas scale as the square of the side-length ratio. Larger area = 54(5/3)² = 54(25/9) = 150.",diagram:{type:"similarAreas",small:"3",large:"5"}
},
{
 id:"G32",topic:"Transformations",level:"Nonroutine",stem:"Point P(−4, 7) is reflected across the y-axis and then translated 3 units downward. What are the coordinates of the final image of P?",choices:["(−4, 4)","(4, 4)","(4, 10)","(−4, 10)"],answer:1,explanation:"Reflecting across the y-axis changes (−4,7) to (4,7). Translating down 3 gives (4,4).",diagram:{type:"transformPoint"}
}
];