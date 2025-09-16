import { useLocation } from "react-router-dom";
import LogCanvas from "../components/LogCanvas";
import MapView from "../components/MapView";

export default function Results() {
  const { state } = useLocation() as any;
  const plan = state?.plan;

  if (!plan) return <p>No plan found. Go back and submit the form.</p>;

  return (
    <div>
      <h2>Results</h2>
      <p>
        <strong>Distance:</strong> {plan.distance_miles.toFixed(1)} mi |{" "}
        <strong>Duration:</strong> {Math.round(plan.duration_minutes / 60)} hrs
      </p>
      <MapView
        polylineEnc={plan.polyline}
        polylines={plan.polylines}
        stops={plan.stops}
      />
      <div style={{ display: "grid", gap: 16, marginTop: 24 }}>
        {plan.logs.map((day: any, idx: number) => (
          <div key={idx}>
            <h3>Day {idx + 1}</h3>
            <div className="log-canvas">
              <LogCanvas blocks={day} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

