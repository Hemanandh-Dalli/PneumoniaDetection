import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Container,
  Typography,
  Card,
  CardContent,
  Button,
  Grid,
} from "@mui/material";
import API from "../api/api";
import Layout from "../components/Layout";
import { motion } from "framer-motion";

function History() {
  const [predictions, setPredictions] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchPredictions = async () => {
      try {
        const res = await API.get("/my-predictions");
        setPredictions(res.data);
      } catch (err) {
        console.error("HISTORY ERROR:", err);
      }
    };

    fetchPredictions();
  }, []);

  return (
    <Layout>
      <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}>
        <Container maxWidth="lg">
          <Typography className="page-title" sx={{ mb: 1 }}>
            Prediction History
          </Typography>
          <Typography className="page-subtitle" sx={{ mb: 4 }}>
            Browse all previous scans and reopen details.
          </Typography>

          {predictions.length === 0 && (
            <Typography>No predictions found.</Typography>
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
                      {item.predicted_class}
                    </Typography>

                    <Typography>
                      {(item.confidence * 100).toFixed(2)}%
                    </Typography>

                    <Button
                      className="cta-btn"
                      variant="contained"
                      sx={{
                        mt: 2,
                        background: "linear-gradient(135deg, #3ad6ff, #41b2ff)",
                      }}
                      onClick={() =>
                        navigate("/result", {
                          state: item,
                        })
                      }
                    >
                      View
                    </Button>
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

export default History;
