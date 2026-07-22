import { describe, expect, it } from "vitest";
import en from "./en/indicators.json";
import fr from "./fr/indicators.json";
import de from "./de/indicators.json";

describe("indicator translations",()=>{
  it("contains fifty translated names and descriptions in every language",()=>{
    const source=Object.keys(en).sort();
    expect(source).toHaveLength(50);
    expect(Object.keys(fr).sort()).toEqual(source);
    expect(Object.keys(de).sort()).toEqual(source);
    for(const resource of [en,fr,de])for(const item of Object.values(resource)){expect(item.name.length).toBeGreaterThan(2);expect(item.description.length).toBeGreaterThan(10)}
  });
});
