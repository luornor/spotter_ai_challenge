import TripForm from "../components/TripForm";

export default function Home() {
  return (
    <div className="container">
      <div style={{display:'flex', justifyContent:'space-between', alignItems:'baseline'}}>
        <h1 className="page-title">Trip Planner</h1>
        <a className="nav-link" href="/">Home</a>
      </div>
      <TripForm />
    </div>
  )
}
