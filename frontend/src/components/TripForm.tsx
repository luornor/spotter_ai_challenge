import { useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import { api } from "../lib/api";


type FormData = {
  current_location: string;
  pickup_location: string;
  dropoff_location: string;
  current_cycle_used_hours: number;
};

function LocationIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
      <path d="M12 22s7-5.5 7-12a7 7 0 1 0-14 0c0 6.5 7 12 7 12z" stroke="#89b4fa" strokeWidth="1.6"/>
      <circle cx="12" cy="10" r="2.8" stroke="#89b4fa" strokeWidth="1.6"/>
    </svg>
  );
}
function ClockIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
      <circle cx="12" cy="12" r="9" stroke="#a6e3a1" strokeWidth="1.6"/>
      <path d="M12 7v6l4 2" stroke="#a6e3a1" strokeWidth="1.6" strokeLinecap="round"/>
    </svg>
  );
}

export default function TripForm() {
  const {
    register,
    handleSubmit,
    formState: { isSubmitting, errors },
    setValue,
  } = useForm<FormData>();
  const navigate = useNavigate();

  const onSubmit = async (data: FormData) => {
    try {
      const plan = await api("/trip/plan/", {
        method: "POST",
        body: JSON.stringify(data),
      });
      navigate("/results", { state: { plan } });
    } catch (e: any) {
      alert(e.message || "Failed to plan trip");
    }
  };

  const fillExample = () => {
    setValue("current_location", "Austin, TX");
    setValue("pickup_location", "Dallas, TX");
    setValue("dropoff_location", "Oklahoma City, OK");
    setValue("current_cycle_used_hours", 10 as any);
  };

  return (
    <div className="form-card">
      <div className="header">
        <h2>Plan a Trip</h2>
        <small>Enter locations and your current cycle hours</small>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="form-grid" noValidate>
        {/* Current location */}
        <label className="label" htmlFor="current_location">Current location</label>
        <div className="input-row">
          <LocationIcon />
          <input
            id="current_location"
            className="input"
            placeholder="e.g. Austin, TX"
            {...register("current_location", { required: "Required" })}
          />
        </div>
        {errors.current_location && <div className="error">{errors.current_location.message}</div>}

        {/* Pickup location */}
        <label className="label" htmlFor="pickup_location">Pickup location</label>
        <div className="input-row">
          <LocationIcon />
          <input
            id="pickup_location"
            className="input"
            placeholder="e.g. Dallas, TX"
            {...register("pickup_location", { required: "Required" })}
          />
        </div>
        {errors.pickup_location && <div className="error">{errors.pickup_location.message}</div>}

        {/* Dropoff location */}
        <label className="label" htmlFor="dropoff_location">Dropoff location</label>
        <div className="input-row">
          <LocationIcon />
          <input
            id="dropoff_location"
            className="input"
            placeholder="e.g. Oklahoma City, OK"
            {...register("dropoff_location", { required: "Required" })}
          />
        </div>
        {errors.dropoff_location && <div className="error">{errors.dropoff_location.message}</div>}

        {/* Hours used in current 70-hour cycle */}
        <label className="label" htmlFor="hours_used">Current cycle used (hours)</label>
        <div className="input-row">
          <ClockIcon />
          <input
            id="hours_used"
            className="input"
            type="number"
            step="0.1"
            placeholder="e.g. 10"
            {...register("current_cycle_used_hours", {
              required: "Required",
              valueAsNumber: true,
              min: { value: 0, message: "Must be ≥ 0" },
              max: { value: 70, message: "Max 70 hours" },
            })}
          />
        </div>
        <div className="hint">Used hours in the 70-hour/8-day cycle.</div>
        {errors.current_cycle_used_hours && (
          <div className="error">{errors.current_cycle_used_hours.message}</div>
        )}

        {/* Actions */}
        <div className="actions">
          <button className="btn btn-primary" disabled={isSubmitting}>
            {isSubmitting ? "Planning…" : "Plan Trip"}
          </button>
          <button
            type="button"
            className="btn btn-ghost"
            onClick={fillExample}
            disabled={isSubmitting}
            title="Prefill example values"
          >
            Use Example
          </button>
        </div>
      </form>
    </div>
  );
}
