// let carOne = {
//   id: 001,
//   color: "red",
//   type: "cabrio",
//   registration: new Date("2016-05-02"),
//   capacity: 2,
// };
// let carTwo = {
//   id: 002,
//   color: "Blue",
//   type: "statin wagon",
//   registration: new Date("2018-02-02"),
//   capacity: 2,
// };

// const cars = [];
// cars.push(carOne);
// cars.push(carTwo);

// const carsIds = [];
// for (const car of cars) {
//   //   console.log(car.color);
//   carsIds.push(car.id);
// }

// let isBase64Encoded = false;
// if (isBase64Encoded === true) {
//   console.log("is encoded");
// } else {
//   console.log("is not encoded");
// }

// console.log(carsIds);

const publicHttpApiRouteKeys = [
  "GET /items",
  "PUT /items",
  "GET /items/{id}",
  "DELETE /items/{id}",
];

publicHttpApiRouteKeys.forEach((item) => {
  let newroute = item.replace(/[^A-Z0-9]/gi, "");
  console.log(newroute);
});
