import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Container,
  Typography,
  Card,
  CardContent,
  Button,
  Box,
  Grid,
} from "@mui/material";
import API from "../api/api";
import Layout from "../components/Layout";
import { motion } from "framer-motion";

function Dashboard() {
  const [predictions, setPredictions] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchPredictions = async () => {
      try {
        const res = await API.get("/my-predictions");
        setPredictions(res.data);
      } catch (err) {
        console.error("DASHBOARD ERROR:", err);
      }
    };

    fetchPredictions();
  }, []);

  return (
    <Layout>
      <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}>
        <Container maxWidth="lg">
          <Typography className="page-title" sx={{ mb: 1 }}>
            Dashboard
          </Typography>
          <Typography className="page-subtitle" sx={{ mb: 3 }}>
            Review your latest pneumonia screening outputs.
          </Typography>

          <Button
            className="cta-btn"
            variant="contained"
            sx={{
              mb: 4,
              background: "linear-gradient(135deg, #3ad6ff, #41b2ff)",
            }}
            onClick={() => navigate("/")}
          >
            Upload New X-ray
          </Button>

          <Typography className="section-title" sx={{ mb: 3 }}>
            Recent Predictions
          </Typography>

          {predictions.length === 0 && (
            <Typography>No predictions yet. Upload an X-ray to get started.</Typography>
          )}

          <Grid container spacing={3}>
            {predictions.map((item) => (
              <Grid item xs={12} md={4} key={item.id}>
                <Card
                  className="glass-3d float-card"
                  sx={{ color: "#eff7ff", backgroundColor: "transparent" }}
                >
                  <CardContent>
                    <Typography>
                      <strong>Diagnosis:</strong> {item.predicted_class}
                    </Typography>

                    <Typography>
                      <strong>Confidence:</strong>{" "}
                      {(item.confidence * 100).toFixed(2)}%
                    </Typography>

                    <Typography sx={{ mt: 1 }}>
                      <strong>Date:</strong>{" "}
                      {new Date(item.created_at).toLocaleString()}
                    </Typography>

                    <Box sx={{ mt: 2 }}>
                      <Button
                        className="cta-btn"
                        variant="contained"
                        sx={{
                          background: "linear-gradient(135deg, #3ad6ff, #41b2ff)",
                        }}
                        onClick={() =>
                          navigate("/result", {
                            state: {
                              predicted_class: item.predicted_class,
                              confidence: item.confidence,
                              chat_id: item.chat_id,
                              image_path: item.image_path,
                            },
                          })
                        }
                      >
                        View Details
                      </Button>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Container>
      </motion.div>
    </Layout>
  );
}

export default Dashboard;
