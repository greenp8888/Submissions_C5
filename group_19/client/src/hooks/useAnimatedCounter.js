import { useEffect, useRef, useState } from "react";

export function useAnimatedCounter(target, duration = 1200) {
  const [value, setValue] = useState(0);
  const frameRef = useRef(null);
  const startRef = useRef(null);

  useEffect(() => {
    if (target == null) return;
    const start = 0;
    const end = parseFloat(target) || 0;

    const animate = (ts) => {
      if (!startRef.current) startRef.current = ts;
      const elapsed = ts - startRef.current;
      const progress = Math.min(elapsed / duration, 1);
      // Ease out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      setValue(start + (end - start) * eased);
      if (progress < 1) {
        frameRef.current = requestAnimationFrame(animate);
      }
    };

    startRef.current = null;
    frameRef.current = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(frameRef.current);
  }, [target, duration]);

  return value;
}
