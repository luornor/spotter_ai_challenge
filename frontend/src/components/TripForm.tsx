import { useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import { api } from "../lib/api";

type FormData = {
  current_location: string;
  pickup_location: string;
  dropoff_location: string;
  current_cycle_used_hours: number;
};

export default function TripForm() {
  const {
    register,
    handleSubmit,
    formState: { isSubmitting },
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

  return (
    <form
      onSubmit={handleSubmit(onSubmit)}
      style={{ display: "grid", gap: 12, maxWidth: 640 }}
    >
      <input
        placeholder="Current location"
        {...register("current_location", { required: true })}
      />
      <input
        placeholder="Pickup location"
        {...register("pickup_location", { required: true })}
      />
      <input
        placeholder="Dropoff location"
        {...register("dropoff_location", { required: true })}
      />
      <input
        type="number"
        step="0.1"
        placeholder="Current cycle used (hrs)"
        {...register("current_cycle_used_hours", {
          required: true,
          valueAsNumber: true,
        })}
      />
      <button disabled={isSubmitting}>
        {isSubmitting ? "Planning…" : "Plan Trip"}
      </button>
    </form>
  );
}
