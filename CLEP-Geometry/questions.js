window.GEOMETRY_QUESTIONS = [
{
 id:"G01",topic:"Triangles",level:"Layered",stem:"In isosceles triangle ABC, AB = AC = 25 and BC = 14. Point D is the midpoint of BC, and segment AD is drawn. What is the area of triangle ABC?",choices:["84","168","175","336"],answer:1,explanation:"Because the triangle is isosceles and D is the midpoint of the base, median AD is also an altitude. Thus BD = 7. From right triangle ABD, AD = √(25²−7²) = 24. Area = (1/2)(14)(24) = 168.",diagram:{type:"median"}
},
{
 id:"G02",topic:"Triangles",level:"Layered",stem:"In isosceles triangle PQR, PQ = PR = 13. Altitude PS is drawn to base QR, and QR = 10. What is the area of triangle PQR?",choices:["30","50","60","120"],answer:2,explanation:"In an isosceles triangle, the altitude from the vertex also bisects the base, so QS = 5. Then PS = √(13²−5²) = 12. Area = (1/2)(10)(12) = 60.",diagram:{type:"altitude"}
},
{
 id:"G03",topic:"Triangles",level:"Layered",stem:"In triangle ABC, side AC is extended through C. The exterior angle at C is 124°. If AB = BC, what is the measure of angle B?",choices:["56°","62°","68°","124°"],answer:2,explanation:"The interior angle at C is 180°−124° = 56°. Since AB = BC, the angles opposite those sides, A and C, are equal, so angle A = 56°. Therefore angle B = 180°−56°−56° = 68°.",diagram:{type:"exterior",a:"?",ext:"124°"}
},
{
 id:"G04",topic:"Triangles",level:"Layered",stem:"An isosceles triangle has two equal sides of length 10 and a base of length 16. What is the area of the triangle?",choices:["40","48","60","80"],answer:1,explanation:"The altitude from the vertex bisects the base into two segments of 8. The height is √(10²−8²) = 6. Area = (1/2)(16)(6) = 48.",diagram:{type:"triangleHeight",base:"16",height:"?"}
},
{
 id:"G05",topic:"Triangles",level:"Layered",stem:"The side lengths of a right triangle are in the ratio 3:4:5. If the hypotenuse is 20, what is the area of the triangle?",choices:["48","80","96","192"],answer:2,explanation:"Since 5k = 20, k = 4. The legs are 12 and 16. Area = (1/2)(12)(16) = 96.",diagram:{type:"rightTriangle",a:"3k",b:"4k",c:"20"}
},
{
 id:"G06",topic:"Circles",level:"Layered",stem:"The figure below shows a sector of a circle. The length of arc AB is 18 units, and the measure of central angle AOB is 45°. What is the area of sector AOB?",choices:["324/π","648/π","162π","324π"],answer:1,explanation:"First derive the radius. Since 45° = π/4 radians, 18 = r(π/4), giving r = 72/π. Sector area can then be found from (1/2)rs: (1/2)(72/π)(18) = 648/π.",diagram:{type:"sector",angle:"45°",arc:"18"}
},
{
 id:"G07",topic:"Circles",level:"Layered",stem:"A square is inscribed in a circle. The side length of the square is 10√2. An arc of the circle subtends a central angle of 72°. What is the length of the arc?",choices:["2π","4π","5π","8π"],answer:1,explanation:"The diagonal of the inscribed square is the diameter of the circle. Its diagonal is (10√2)(√2) = 20, so the radius is 10. A 72° arc is 1/5 of the circumference, so its length is (1/5)(20π) = 4π.",diagram:{type:"arc",angle:"72°",radius:"?"}
},
{
 id:"G08",topic:"Circles",level:"Layered",stem:"Two concentric circles form a shaded ring. The inner circle has diameter 12, and the ring is 4 units wide. What is the area of the shaded ring?",choices:["36π","48π","64π","100π"],answer:2,explanation:"The inner radius is 6. Since the ring is 4 units wide, the outer radius is 10. The shaded area is π(10²−6²) = 64π.",diagram:{type:"annulus",outer:"?",inner:"6"}
},
{
 id:"G09",topic:"Triangles",level:"Layered",stem:"In triangle ABC, AD bisects angle A and meets BC at D. If AB = 12, AC = 18, and BD = 8, what is the perimeter of triangle ABC?",choices:["42","46","50","54"],answer:2,explanation:"By the angle-bisector theorem, BD/DC = AB/AC = 12/18 = 2/3. Since BD = 8, DC = 12. Thus BC = 20, and the perimeter is 12 + 18 + 20 = 50.",diagram:{type:"angleBisector",left:"12",right:"18",bd:"8",dc:"?"}
},
{
 id:"G10",topic:"Similarity",level:"Layered",stem:"Two triangles are similar. A side of length 7 in the smaller triangle corresponds to a side of length 21 in the larger triangle. If the area of the smaller triangle is 40 square units, what is the area of the larger triangle?",choices:["120","240","360","840"],answer:2,explanation:"The side scale factor is 21/7 = 3. Areas scale by the square of the side factor, so the area scale factor is 9. The larger area is 40(9) = 360.",diagram:{type:"similar",small1:"7",large1:"21",small2:"Area 40",large2:"?"}
},
{
 id:"G11",topic:"Lines & Angles",level:"Layered",stem:"Parallel lines l and m are cut by a transversal. A 68° angle and angle x are same-side interior angles. Angle x is also an exterior angle of an isosceles triangle whose two remote interior angles are congruent. What is the measure of each of those congruent angles?",choices:["34°","56°","68°","112°"],answer:1,explanation:"Same-side interior angles are supplementary, so x = 180°−68° = 112°. An exterior angle equals the sum of the two remote interior angles. Since they are equal, each is 112°/2 = 56°.",diagram:{type:"parallel",angle:"68°",x:"x"}
},
{
 id:"G12",topic:"Polygons",level:"Layered",stem:"Each exterior angle of a regular polygon measures 45°. How many diagonals does the polygon have?",choices:["16","20","24","28"],answer:1,explanation:"The exterior angles sum to 360°, so the polygon has 360/45 = 8 sides. The number of diagonals is 8(8−3)/2 = 20.",diagram:{type:"regularPolygon",sides:8,label:"45°"}
},
{
 id:"G13",topic:"Polygons",level:"Layered",stem:"Each interior angle of a regular polygon measures 156°. How many diagonals does the polygon have?",choices:["75","90","105","120"],answer:1,explanation:"Each exterior angle is 180°−156° = 24°, so the polygon has 360/24 = 15 sides. The number of diagonals is 15(12)/2 = 90.",diagram:{type:"regularPolygon",sides:15,label:"156°"}
},
{
 id:"G14",topic:"Coordinate Geometry",level:"Layered",stem:"Points A(−2, 3) and B(4, 11) are endpoints of a diameter of a circle. What is the area of the circle?",choices:["10π","20π","25π","100π"],answer:2,explanation:"The diameter is the distance AB = √(6²+8²) = 10. Therefore the radius is 5, and the area is 25π.",diagram:{type:"coordinate",points:[[-2,3,"A"],[4,11,"B"]]}
},
{
 id:"G15",topic:"Coordinate Geometry",level:"Layered",stem:"Points A(−5, 8) and C(7, −4) are opposite vertices of a rectangle. At what point do the two diagonals of the rectangle intersect?",choices:["(1, 2)","(2, 1)","(−1, 2)","(1, −2)"],answer:0,explanation:"The diagonals of a rectangle bisect each other. Their intersection is therefore the midpoint of AC: ((−5+7)/2, (8−4)/2) = (1,2).",diagram:{type:"coordinate",points:[[-5,8,"A"],[7,-4,"C"]]}
},
{
 id:"G16",topic:"Coordinate Geometry",level:"Layered",stem:"A line passes through (2, −1) and (6, 7). A second line is perpendicular to the first and passes through (6, 7). At what x-coordinate does the second line cross the x-axis?",choices:["10","14","18","20"],answer:3,explanation:"The first line has slope 2, so the perpendicular slope is −1/2. Its equation through (6,7) is y−7 = −(1/2)(x−6). Set y = 0: −7 = −(1/2)(x−6), so x = 20.",diagram:null
},
{
 id:"G17",topic:"Quadrilaterals",level:"Layered",stem:"The length and width of a rectangle are in the ratio 12:5. If the diagonal of the rectangle is 26, what is the perimeter of the rectangle?",choices:["52","60","68","78"],answer:2,explanation:"The ratio 5:12:13 forms a right triangle. A diagonal of 26 means the scale factor is 2, so the dimensions are 10 and 24. The perimeter is 2(10+24) = 68.",diagram:{type:"rectangleDiagonal",w:"12k",h:"5k",d:"26"}
},
{
 id:"G18",topic:"Quadrilaterals",level:"Layered",stem:"An isosceles trapezoid has bases of lengths 12 and 22 and legs of length 13. What is the area of the trapezoid?",choices:["156","180","204","221"],answer:2,explanation:"Because the trapezoid is isosceles, the 10-unit difference between the bases splits equally, giving a 5-unit horizontal leg on each side. The height is √(13²−5²) = 12. Area = (1/2)(12+22)(12) = 204.",diagram:{type:"trapezoid",b1:"12",b2:"22",h:"?"}
},
{
 id:"G19",topic:"Quadrilaterals",level:"Layered",stem:"A rhombus has side length 13. One diagonal has length 10. What is the area of the rhombus?",choices:["60","100","120","240"],answer:2,explanation:"The diagonals of a rhombus are perpendicular bisectors. Half of the known diagonal is 5. Using a right triangle with hypotenuse 13, half of the other diagonal is √(13²−5²) = 12, so the other diagonal is 24. Area = (1/2)(10)(24) = 120.",diagram:{type:"rhombus",d1:"10",d2:"?"}
},
{
 id:"G20",topic:"Solid Geometry",level:"Layered",stem:"The circumference of the base of a right circular cylinder is 10π. The height of the cylinder is equal to the diameter of its base. What is the volume of the cylinder?",choices:["100π","200π","250π","500π"],answer:2,explanation:"From 2πr = 10π, r = 5. The diameter is 10, so the height is 10. Volume = π(5²)(10) = 250π.",diagram:{type:"cylinder",r:"?",h:"diameter"}
},
{
 id:"G21",topic:"Solid Geometry",level:"Layered",stem:"A rectangular prism has base dimensions 6 by 8. Its space diagonal is 26. What is the volume of the prism?",choices:["480","960","1,152","1,248"],answer:2,explanation:"The base diagonal is √(6²+8²) = 10. The space diagonal, base diagonal, and height form a right triangle, so h = √(26²−10²) = 24. Volume = 6·8·24 = 1,152.",diagram:{type:"prism",a:"6",b:"8",c:"space diagonal 26"}
},
{
 id:"G22",topic:"Solid Geometry",level:"Layered",stem:"A right circular cone has radius 5 and slant height 13. What is the volume of the cone?",choices:["60π","100π","120π","300π"],answer:1,explanation:"The radius, height, and slant height form a right triangle. Thus h = √(13²−5²) = 12. Volume = (1/3)π(5²)(12) = 100π.",diagram:{type:"cone",r:"5",h:"?"}
},
{
 id:"G23",topic:"Composite Figures",level:"Layered",stem:"A circle is inscribed in a square whose perimeter is 56. What is the total area inside the square but outside the circle?",choices:["196−98π","196−49π","56−14π","196−14π"],answer:1,explanation:"The square side is 56/4 = 14. An inscribed circle has diameter equal to the square's side, so r = 7. The shaded area is 14²−π(7²) = 196−49π.",diagram:{type:"squareCircle",side:"perimeter 56"}
},
{
 id:"G24",topic:"Composite Figures",level:"Layered",stem:"A rectangle has perimeter 68 and height 14. A semicircle whose diameter equals the height is removed from each of the two shorter sides. What is the area of the remaining region?",choices:["280−98π","280−49π","238−49π","280+49π"],answer:1,explanation:"From 2(w+14)=68, w=20. The rectangle area is 280. Each semicircle has radius 7; together they form one full circle of area 49π. Remaining area = 280−49π.",diagram:{type:"doubleSemi",w:"?",h:"14"}
},
{
 id:"G25",topic:"Composite Figures",level:"Layered",stem:"A figure consists of an 18-by-12 rectangle topped by an isosceles triangle. The triangle has base 18 and equal sides 15. A circular opening of radius 3 is removed from the rectangle. What is the area of the remaining figure?",choices:["288−9π","306−9π","324−9π","324−18π"],answer:2,explanation:"The altitude of the isosceles roof bisects its 18-unit base into two 9-unit segments. Its height is √(15²−9²)=12, so roof area is 108. Rectangle area is 216, and the circular opening has area 9π. Total = 216+108−9π = 324−9π.",diagram:{type:"houseHole",w:"18",rectH:"12",triH:"?",r:"3"}
},
{
 id:"G26",topic:"Composite Figures",level:"Layered",stem:"A square has diagonal 12√2. From each corner, a quarter-circle is drawn with radius equal to one-half the side length. What is the area inside the square but outside the four quarter-circles?",choices:["144−18π","144−36π","72−36π","288−36π"],answer:1,explanation:"For a square, diagonal = side·√2, so the side is 12. Each quarter-circle has radius 6. Four quarter-circles make one full circle of radius 6, area 36π. The remaining area is 144−36π.",diagram:{type:"quarterSquare",side:"d=12√2",r:"?"}
},
{
 id:"G27",topic:"Composite Figures",level:"Layered",stem:"A right triangle with legs 6 and 8 is inscribed in a semicircle so that its hypotenuse is the diameter. What is the area inside the semicircle but outside the triangle?",choices:["25π/2−24","25π−24","25π/2−48","50π−24"],answer:0,explanation:"The hypotenuse is √(6²+8²)=10, so the semicircle radius is 5. Semicircle area = (1/2)π(5²)=25π/2. Triangle area = (1/2)(6)(8)=24. Difference = 25π/2−24.",diagram:{type:"semiTriangle",a:"6",b:"8",d:"?"}
},
{
 id:"G28",topic:"Circles",level:"Layered",stem:"Points A, B, and C lie on a circle with center O. Central angle AOC measures 136°. If AB = BC, what is the measure of angle BAC?",choices:["34°","56°","68°","112°"],answer:1,explanation:"Inscribed angle ABC intercepting arc AC is half the 136° central angle, so angle ABC = 68°. Since AB = BC, triangle ABC is isosceles and angles A and C are equal. Each is (180°−68°)/2 = 56°.",diagram:{type:"inscribed",central:"136°",inscribed:"68°"}
},
{
 id:"G29",topic:"Circles",level:"Layered",stem:"From external point P, segment PT is tangent to a circle at T. The radius OT is 5 and OP = 13. What is the perimeter of triangle OPT?",choices:["25","30","31","36"],answer:1,explanation:"A radius to a tangent is perpendicular at T, so triangle OPT is right. PT = √(13²−5²)=12. The perimeter is 5+12+13 = 30.",diagram:{type:"tangent",r:"5",hyp:"13",tan:"?"}
},
{
 id:"G30",topic:"Polygons",level:"Layered",stem:"Each interior angle of a regular polygon measures 150°. How many diagonals does the polygon have?",choices:["44","48","54","66"],answer:2,explanation:"The exterior angle is 180°−150°=30°, so the polygon has 360/30 = 12 sides. The number of diagonals is 12(12−3)/2 = 54.",diagram:{type:"polygon12"}
},
{
 id:"G31",topic:"Similarity",level:"Layered",stem:"Two similar figures have corresponding sides of lengths 12 and 20. If the area of the smaller figure is 54 square units, what is the area of the larger figure?",choices:["90","120","150","250"],answer:2,explanation:"The side-length scale factor is 20/12 = 5/3. Areas scale by the square, so the larger area is 54(5/3)² = 54(25/9) = 150.",diagram:{type:"similarAreas",small:"12",large:"20"}
},
{
 id:"G32",topic:"Transformations",level:"Layered",stem:"Point P(−4, 7) is reflected across the y-axis and then translated 3 units downward. What is the distance from the origin to the final image of P?",choices:["4","4√2","5","8"],answer:1,explanation:"Reflection across the y-axis sends P to (4,7). Translating down 3 gives (4,4). The distance from the origin is √(4²+4²)=√32=4√2.",diagram:{type:"transformPoint"}
}
];