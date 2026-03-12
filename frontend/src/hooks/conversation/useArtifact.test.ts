import { renderHook, act } from "@testing-library/react";
import { useArtifact } from "./useArtifact";

describe("useArtifact", () => {
  const mockArtifact = {
    id: "1",
    version: 1,
    content: "test content",
    title: "test title",
  };

  it("初期状態確認", () => {
    const { result } = renderHook(() => useArtifact());
    expect(result.current.artifact).toBeNull();
    expect(result.current.artifactHistory).toEqual([]);
    expect(result.current.latestArtifact).toBeNull();
  });

  it("リセット確認", () => {
    const { result } = renderHook(() => useArtifact());

    act(() => {
      result.current.setArtifact(mockArtifact);
    });
    expect(result.current.artifact).toEqual(mockArtifact);

    act(() => {
      result.current.resetArtifact();
    });
    expect(result.current.artifact).toBeNull();
  });

  it("History追加確認", () => {
    const { result } = renderHook(() => useArtifact());

    act(() => {
      result.current.addArtifactHistory(mockArtifact);
    });
    expect(result.current.artifactHistory).toEqual([mockArtifact]);
  });

  it("配列型History追加確認", () => {
    const { result } = renderHook(() => useArtifact());
    const artifacts = [mockArtifact, { ...mockArtifact, id: "2" }];

    act(() => {
      result.current.addArtifactHistory(artifacts);
    });
    expect(result.current.artifactHistory).toEqual(artifacts);
  });

  it("getArtifactByIdAndVersion確認", () => {
    const { result } = renderHook(() => useArtifact());
    const artifacts = [mockArtifact, { ...mockArtifact, id: "2", version: 2 }];

    act(() => {
      result.current.addArtifactHistory(artifacts);
    });

    expect(result.current.getArtifactByIdAndVersion("1", 1)).toEqual(mockArtifact);
    expect(result.current.getArtifactByIdAndVersion("2", 2)).toEqual(artifacts[1]);
    expect(result.current.getArtifactByIdAndVersion("3", 1)).toBeNull();
  });

  it("getMaxVersionById確認", () => {
    const { result } = renderHook(() => useArtifact());
    const artifacts = [
      { ...mockArtifact, id: "1", version: 1 },
      { ...mockArtifact, id: "1", version: 2 },
      { ...mockArtifact, id: "2", version: 1 },
    ];

    act(() => {
      result.current.addArtifactHistory(artifacts);
    });

    expect(result.current.getMaxVersionById("1")).toBe(2);
    expect(result.current.getMaxVersionById("2")).toBe(1);
    expect(result.current.getMaxVersionById("3")).toBe(1);
  });
});
