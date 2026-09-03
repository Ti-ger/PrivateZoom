import assert from "node:assert/strict";
import test from "node:test";

import {
    getNextAbstractionIndex,
    getUniqueColumnValues,
    getUniqueValuesByOrder,
} from "../webapp/static/utils/processData.mjs";

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

test("filter values come from the currently abstracted events", () => {
    const events = [
        {Activity: "checking"},
        {Activity: "decision"},
        {Activity: "checking"},
    ];

    assert.deepEqual(
        getUniqueColumnValues(events, "Activity"),
        ["checking", "decision"],
    );
});

test("specific zoom defaults to the next more detailed abstraction", () => {
    const possible = [
        "Activity_abstracted",
        "Activity_level1",
        "Activity_level2",
        "Activity_not_abstracted",
    ];

    assert.equal(
        getNextAbstractionIndex(possible, ["Activity_level1"]),
        2,
    );
    assert.equal(
        getNextAbstractionIndex(possible, ["Activity_level2"]),
        3,
    );
});
