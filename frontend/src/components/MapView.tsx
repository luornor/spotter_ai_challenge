import { useEffect, useRef } from "react";
import L from "leaflet";
import poly from "polyline";

export default function MapView({
  polylineEnc,
  polylines,
  stops,
}: {
  polylineEnc?: string;
  polylines?: string[];
  stops: any[];
}) {
  const ref = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<L.Map | null>(null);

  useEffect(() => {
    if (!ref.current) return;

    if (!mapRef.current) {
      mapRef.current = L.map(ref.current);
      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: "&copy; OpenStreetMap contributors",
      }).addTo(mapRef.current);
    }
    const map = mapRef.current!;

    // remove all non-tile layers
    map.eachLayer((layer: any) => {
      if (!(layer instanceof L.TileLayer)) map.removeLayer(layer);
    });

    const routes: L.Polyline[] = [];
    const draw = (enc: string) => {
      try {
        const coords = poly.decode(enc) as [number, number][]; // [[lat, lng], ...]
        const latlngs: L.LatLngTuple[] = coords.map((c) => [c[0], c[1]]);
        if (latlngs.length) routes.push(L.polyline(latlngs).addTo(map));
      } catch (e) {
        console.warn("Invalid polyline", e);
      }
    };

    if (Array.isArray(polylines) && polylines.length) polylines.forEach(draw);
    else if (polylineEnc) draw(polylineEnc);

    if (routes.length) {
      const group = L.featureGroup(routes);
      map.fitBounds(group.getBounds(), { padding: [20, 20] });
    }

    stops?.forEach((s) => {
      L.marker([s.lat, s.lng])
        .addTo(map)
        .bindPopup(`${s.type.toUpperCase()}: ${s.name}`);
    });
  }, [polylineEnc, JSON.stringify(polylines), JSON.stringify(stops)]);

  return (
    <div
      ref={ref}
      style={{
        height: 380,
        width: "100%",
        borderRadius: 8,
        overflow: "hidden",
        border: "1px solid #eee",
        marginTop: 12,
      }}
    />
  );
}
