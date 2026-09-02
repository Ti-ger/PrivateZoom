import assert from "node:assert/strict";
import test from "node:test";

import {getUniqueValuesByOrder} from "../webapp/static/utils/processData.mjs";

const value = (event) => event.activity;
const order = (event) => event.__activity_order.Activity;

test("orders activities from earliest to latest on a horizontal axis", () => {
    const events = [
        {activity: "finish", __activity_order: {Activity: 3}},
        {activity: "start", __activity_order: {Activity: 1}},
        {activity: "middle", __activity_order: {Activity: 2}},
        {activity: "middle", __activity_order: {Activity: 2}},
    ];

    assert.deepEqual(
        getUniqueValuesByOrder(events, value, order),
        ["start", "middle", "finish"],
    );
});

test("reverses the domain so earliest activities appear at the top vertically", () => {
    const events = [
        {activity: "start", __activity_order: {Activity: 1}},
        {activity: "finish", __activity_order: {Activity: 3}},
        {activity: "middle", __activity_order: {Activity: 2}},
    ];

    assert.deepEqual(
        getUniqueValuesByOrder(events, value, order, true),
        ["finish", "middle", "start"],
    );
});

test("uses labels as a deterministic tie-breaker", () => {
    const events = [
        {activity: "beta", __activity_order: {Activity: 1}},
        {activity: "alpha", __activity_order: {Activity: 1}},
    ];

    assert.deepEqual(
        getUniqueValuesByOrder(events, value, order),
        ["alpha", "beta"],
    );
});
