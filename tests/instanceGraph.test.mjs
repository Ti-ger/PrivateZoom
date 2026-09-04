import assert from "node:assert/strict";
import test from "node:test";

globalThis.d3 = {
    isoParse: (value) => new Date(value),
    timeFormat: () => (value) => String(value),
};

const {buildTooltipHtml} = await import(
    "../webapp/static/charts/instanceGraph.mjs"
);


test("case identifiers are excluded from event tooltips", () => {
    const accessors = {
        Activity: (event) => event.Activity,
        "case:concept:name": (event) => event["case:concept:name"],
    };

    const html = buildTooltipHtml([{
        Activity: "register request",
        "case:concept:name": "sensitive-case-id",
    }], accessors);

    assert.match(html, /Activity/);
    assert.match(html, /register request/);
    assert.doesNotMatch(html, /case:concept:name/);
    assert.doesNotMatch(html, /sensitive-case-id/);
});
