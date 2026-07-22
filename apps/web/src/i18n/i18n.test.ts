import { describe, expect, it } from "vitest";
import en from "./en/translation.json";
import fr from "./fr/translation.json";
import de from "./de/translation.json";

function leafKeys(value:unknown,prefix=""):string[]{if(typeof value!=="object"||value===null)return [prefix];return Object.entries(value).flatMap(([key,child])=>leafKeys(child,prefix?`${prefix}.${key}`:key))}

describe("translation resources",()=>{
  it("keeps French and German at parity with the English source keys",()=>{
    const source=leafKeys(en).sort();
    expect(leafKeys(fr).sort()).toEqual(source);
    expect(leafKeys(de).sort()).toEqual(source);
  });
});
