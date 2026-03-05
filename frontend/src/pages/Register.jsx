import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Container, Typography, TextField, Button, Box } from "@mui/material";
import API from "../api/api";

function Register() {
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleRegister = async () => {
    if (!email || !password) {
      alert("Please fill all fields");
      return;
    }

    try {
      await API.post("/register", {
        email: email,
        password: password,
      });

      alert("Registration successful. Please login.");
      navigate("/login");
    } catch (err) {
      console.error("REGISTER ERROR:", err);
      alert(err.response?.data?.detail || "Registration failed");
    }
  };

  return (
    <Box className="auth-shell">
      <Container maxWidth="sm" className="glass-3d float-card" sx={{ p: { xs: 3, md: 4 } }}>
        <Typography className="page-title" gutterBottom>
          Create Account
        </Typography>

        <Typography className="page-subtitle" sx={{ mb: 3 }}>
          Set up your clinical dashboard access.
        </Typography>

        <Box sx={{ mt: 2 }}>
          <TextField
            fullWidth
            label="Email"
            sx={{ mb: 3 }}
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />

          <TextField
            fullWidth
            label="Password"
            type="password"
            sx={{ mb: 3 }}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />

          <Button
            className="cta-btn"
            variant="contained"
            fullWidth
            sx={{
              background: "linear-gradient(135deg, #3ad6ff, #41b2ff)",
            }}
            onClick={handleRegister}
          >
            Register
          </Button>
        </Box>
      </Container>
    </Box>
  );
}

export default Register;
