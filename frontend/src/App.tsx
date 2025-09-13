import { Outlet, Link } from "react-router-dom";

export default function App() {
  return (
    <div style={{ maxWidth: 960, margin: "0 auto", padding: 24 }}>
      <header
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <h1>Trip Planner</h1>
        <nav>
          <Link to="/">Home</Link>
        </nav>
      </header>
      <Outlet />
    </div>
  );
}
