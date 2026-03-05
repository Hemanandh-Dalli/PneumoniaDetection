import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Container, TextField, Button, Typography, Box } from "@mui/material";
import API from "../api/api";

function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const navigate = useNavigate();

  const handleLogin = async () => {
    try {
      const formData = new URLSearchParams();
      formData.append("username", email);
      formData.append("password", password);

      const res = await API.post("/login", formData, {
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
      });

      localStorage.setItem("token", res.data.access_token);
      navigate("/");
    } catch (err) {
      alert("Invalid credentials");
    }
  };

  return (
    <Box className="auth-shell">
      <Container maxWidth="sm" className="glass-3d float-card" sx={{ p: { xs: 3, md: 4 } }}>
        <Typography className="page-title" gutterBottom>
          Secure Login
        </Typography>

        <Typography className="page-subtitle" sx={{ mb: 3 }}>
          Access your pneumonia detection workspace.
        </Typography>

        <TextField
          fullWidth
          label="Email"
          sx={{ mt: 2 }}
          onChange={(e) => setEmail(e.target.value)}
        />

        <TextField
          fullWidth
          label="Password"
          type="password"
          sx={{ mt: 2 }}
          onChange={(e) => setPassword(e.target.value)}
        />

        <Button
          className="cta-btn"
          fullWidth
          variant="contained"
          sx={{
            mt: 3,
            background: "linear-gradient(135deg, #3ad6ff, #41b2ff)",
          }}
          onClick={handleLogin}
        >
          Login
        </Button>

        <Button sx={{ mt: 2, color: "#b7cce4" }} onClick={() => navigate("/register")}>
          Don't have an account? Register
        </Button>
      </Container>
    </Box>
  );
}

export default Login;
