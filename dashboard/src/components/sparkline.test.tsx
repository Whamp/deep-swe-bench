import { describe, it, expect } from "vitest";
import { render } from "@testing-library/react";
import { Sparkline } from "@/components/sparkline";

describe("Sparkline", () => {
  it("renders a polyline path when given >=2 finite points", () => {
    const { container } = render(
      <Sparkline data={[1, 3, 2, 5, 4]} width={100} height={30} ariaLabel="trend" />,
    );
    const svg = container.querySelector("svg");
    expect(svg).not.toBeNull();
    const paths = svg!.querySelectorAll("path");
    // At least the line path is present.
    expect(paths.length).toBeGreaterThanOrEqual(1);
    const line = Array.from(paths).find((p) => p.getAttribute("stroke"));
    expect(line).toBeTruthy();
    expect(svg!.getAttribute("role")).toBe("img");
  });

  it("renders a dashed placeholder when fewer than 2 finite points", () => {
    const { container } = render(<Sparkline data={[42]} ariaLabel="trend" />);
    const svg = container.querySelector("svg");
    const line = svg!.querySelector("line");
    expect(line).not.toBeNull(); // the dashed "no data" line
    expect(svg!.querySelectorAll("path").length).toBe(0);
  });

  it("skips null gaps without crashing", () => {
    const { container } = render(<Sparkline data={[1, null, 3, undefined, 5]} ariaLabel="gappy" />);
    expect(container.querySelector("svg")).not.toBeNull();
  });

  it("draws a behind series when provided", () => {
    const { container } = render(
      <Sparkline data={[1, 2, 3]} behind={[1, 2, 4]} ariaLabel="dual" />,
    );
    const paths = container.querySelector("svg")!.querySelectorAll("path");
    // fill area + behind line + main line
    expect(paths.length).toBeGreaterThanOrEqual(2);
  });

  it("uses a fixed domain for percentage plots", () => {
    const { container } = render(
      <Sparkline data={[0.4, 0.5, 0.6]} domain={[0, 1]} width={100} height={30} ariaLabel="rate" />,
    );
    const line = Array.from(container.querySelectorAll("path")).find((path) =>
      path.hasAttribute("stroke"),
    );
    // With a fixed 0–1 domain, 0.4 starts around y=17.7 rather than filling
    // the full chart height as it would under auto-scaling.
    expect(line?.getAttribute("d")).toContain("M0.0 17.7");
  });
});
