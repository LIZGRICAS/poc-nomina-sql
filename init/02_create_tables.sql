-- Script 02: Crear tablas en PruebaNomina
USE PruebaNomina;
GO

-- Tabla de registros válidos (destino principal)
IF NOT EXISTS (
    SELECT * FROM sys.tables WHERE name = 'Novedades_HorasExtras'
)
BEGIN
    CREATE TABLE Novedades_HorasExtras (
        IdNovedad          INT IDENTITY(1,1) PRIMARY KEY,
        DocumentoEmpleado  VARCHAR(20)   NOT NULL,
        TipoHoraExtra      VARCHAR(50)   NOT NULL,
        CantidadHoras      DECIMAL(5,2)  NOT NULL,
        FechaReporte       DATE          NOT NULL,
        FechaProcesamiento DATETIME      DEFAULT GETDATE(),
        EstadoValidacion   VARCHAR(20)   DEFAULT 'EXITOSO'
    );
END
GO

-- Tabla de errores (trazabilidad de registros rechazados)
IF NOT EXISTS (
    SELECT * FROM sys.tables WHERE name = 'Novedades_HorasExtras_Errores'
)
BEGIN
    CREATE TABLE Novedades_HorasExtras_Errores (
        IdError            INT IDENTITY(1,1) PRIMARY KEY,
        DocumentoEmpleado  VARCHAR(20),
        TipoHoraExtra      VARCHAR(50),
        CantidadHoras      VARCHAR(20),   -- valor crudo sin parsear
        FechaReporte       VARCHAR(20),   -- valor crudo sin parsear
        MotivoError        VARCHAR(500)   NOT NULL,
        FechaProcesamiento DATETIME       DEFAULT GETDATE()
    );
END
GO
