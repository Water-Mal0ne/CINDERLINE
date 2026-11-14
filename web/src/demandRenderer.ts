/** Render only after a change; suspend queued work while a canvas is not visible. */
export function createDemandRenderer(
  draw: () => boolean,
  requestFrame: (callback: () => void) => number,
  cancelFrame: (id: number) => void,
) {
  let frame: number | null = null;
  let active = false;
  let dirty = false;
  let disposed = false;
  const schedule = () => {
    if (!disposed && active && dirty && frame === null) frame = requestFrame(render);
  };
  function render() {
    frame = null;
    if (disposed || !active || !dirty) return;
    dirty = false;
    // OrbitControls returns true while movement/damping still changes the view.
    if (draw()) dirty = true;
    schedule();
  }
  return {
    invalidate() {dirty = true; schedule();},
    setActive(value: boolean) {
      if (disposed) return;
      active = value;
      if (!active && frame !== null) {cancelFrame(frame); frame = null;}
      if (active) {dirty = true; schedule();}
    },
    dispose() {
      disposed = true;
      if (frame !== null) cancelFrame(frame);
      frame = null;
    },
  };
}
